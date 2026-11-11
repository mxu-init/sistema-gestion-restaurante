"""Pytest entry point for the SGR-49 Gherkin scenarios."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
import pytest
from pytest_bdd import scenarios
from sqlalchemy.orm import Session

from app.core.database_connection import get_db, session_local
from app.core.error_translations import handle_db_exceptions
from app.core.handlers import register_exception_handlers
from app.core.logging_config import CorrelationIdMiddleware
from app.main import create_app
from app.models import CategoryModel
from app.schemas.category_schema import CategoryCreate
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.services import reference_service
from tests.step_defs import sgr_49_steps  # noqa: F401

scenarios("features/sgr_49/error_handling.feature")
scenarios("features/sgr_49/correlation_id.feature")
scenarios("features/sgr_49/database_errors.feature")


@pytest.fixture()
def bdd_state() -> dict:
    """Shared response state for one scenario."""
    return {"created_names": []}


@pytest.fixture()
def app_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Real application factory. Startup seeding is not part of these HTTP scenarios."""
    monkeypatch.setattr(reference_service, "ensure_reference_data_on_startup", lambda: None)
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def crash_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    """Second application instance with a route that exists only in this test."""
    monkeypatch.setattr(reference_service, "ensure_reference_data_on_startup", lambda: None)
    application = create_app()

    @application.get("/__bdd/crash", include_in_schema=False)
    def crash() -> dict[str, str]:
        raise RuntimeError("postgresql+psycopg://admin:supersecret@db:5432/prod")

    with TestClient(application, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def db_session(bdd_state: dict) -> Generator[Session, None, None]:
    """Local PostgreSQL session, with categories created by the scenario removed afterwards."""
    session = session_local()
    try:
        yield session
    finally:
        session.rollback()
        names = list(bdd_state["created_names"])
        if names:
            session.query(CategoryModel).filter(CategoryModel.name.in_(names)).delete(
                synchronize_session=False
            )
            session.commit()
        session.close()


@pytest.fixture()
def db_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Test-only route that translates a duplicate category through handle_db_exceptions."""
    application = FastAPI(
        title="SGR BDD Database Integration",
        version="1.0.0",
        responses=COMMON_ERROR_RESPONSES,
    )
    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    application.dependency_overrides[get_db] = _override_get_db

    @application.post("/integration/categories", status_code=status.HTTP_201_CREATED)
    def create_category_db(
        payload: CategoryCreate,
        db: Session = Depends(get_db),
    ) -> dict[str, object]:
        with handle_db_exceptions(db):
            category = CategoryModel(name=payload.name)
            db.add(category)
            db.commit()
            db.refresh(category)
            return {"id": category.id, "name": category.name}

    with TestClient(application, raise_server_exceptions=False) as client:
        yield client
