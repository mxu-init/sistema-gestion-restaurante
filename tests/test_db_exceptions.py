"""Suite de pruebas de integración para la traducción de excepciones de PostgreSQL y manejo de sesiones.

Verifica el flujo completo contra la base de datos PostgreSQL local (`sgr_db`):
  a. SQLSTATE 23505 (Unique Violation) -> ConflictError (HTTP 409) con `{"detail": "Ya existe..."}`.
  b. SQLSTATE 23503 (Foreign Key Violation) -> ConflictError (HTTP 409) con mensaje en español sin filtrar SQL ni nombres de tablas.
  c. Rollback de sesión en `handle_db_exceptions` y `handle_async_db_exceptions` para evitar `PendingRollbackError`.
  d. Integración de `create_app()` con `lifespan` (`ensure_reference_data_on_startup`), `/favicon.ico`, `/health`, `/health/db` y rutas existentes.
"""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock
import uuid

from fastapi import Depends, FastAPI, status
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database_connection import get_db, session_local
from app.core.error_translations import (
    PG_FOREIGN_KEY_VIOLATION,
    PG_UNIQUE_VIOLATION,
    handle_async_db_exceptions,
    handle_db_exceptions,
)
from app.core.exceptions import ConflictError
from app.core.handlers import register_exception_handlers
from app.core.logging_config import CorrelationIdMiddleware
from app.core.reference_data import BASE_CATEGORIES, EU_ALLERGENS
from app.main import create_app
from app.models import CategoryModel, DishModel
from app.schemas.category_schema import CategoryCreate
from app.schemas.dish_schema import DishCreate
from app.schemas.errors import COMMON_ERROR_RESPONSES


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    """Proporciona una sesión real de PostgreSQL limpiando registros creados durante el test."""
    session = session_local()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def integration_app(db_session: Session) -> FastAPI:
    """Aplicación FastAPI conectada a PostgreSQL que delega la integridad a `handle_db_exceptions`."""
    app = FastAPI(
        title="SGR DB Exceptions Integration Test API",
        version="1.0.0",
        responses=COMMON_ERROR_RESPONSES,
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    @app.post("/integration/categories", status_code=status.HTTP_201_CREATED)
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

    @app.post("/integration/dishes", status_code=status.HTTP_201_CREATED)
    def create_dish_db(
        payload: DishCreate,
        db: Session = Depends(get_db),
    ) -> dict[str, object]:
        with handle_db_exceptions(db):
            dish = DishModel(
                name=payload.name,
                description=payload.description,
                price=payload.price or 10.0,
                category_id=payload.category_id,
                is_available=payload.is_available,
            )
            db.add(dish)
            db.commit()
            db.refresh(dish)
            return {"id": dish.id, "name": dish.name, "category_id": dish.category_id}

    return app


@pytest.fixture()
def client(integration_app: FastAPI) -> TestClient:
    """Cliente de pruebas sobre la aplicación de integración con PostgreSQL."""
    return TestClient(integration_app, raise_server_exceptions=False)


def _assert_error_contract_without_sql_leaks(
    response_json: dict[str, object],
    raw_text: str,
) -> str:
    """Verifica el contrato estricto `{"detail": "..."}` y ausencia de fugas SQL o de tablas."""
    assert list(response_json.keys()) == ["detail"]
    detail = response_json["detail"]
    assert isinstance(detail, str)
    assert len(detail.strip()) > 0

    lowered = raw_text.lower()
    forbidden_tokens = (
        "insert into",
        "select ",
        "update ",
        "delete from",
        "categories",
        "dishes",
        "ix_categories_name",
        "dishes_category_id_fkey",
        "psycopg",
        "sqlalchemy",
        "integrityerror",
        "sqlstate",
        "23505",
        "23503",
    )
    for token in forbidden_tokens:
        assert token not in lowered, f"Fuga de detalle técnico detectada en la respuesta: '{token}'"

    return detail


def test_sqlstate_23505_unique_violation_translates_to_409_conflict(
    client: TestClient,
    db_session: Session,
) -> None:
    """a. SQLSTATE 23505 (Unique Violation): crear categoría duplicada en PostgreSQL -> 409 Conflict."""
    unique_category_name = f"Cat_Unica_{uuid.uuid4().hex[:8]}"

    try:
        first_resp = client.post(
            "/integration/categories",
            json={"name": unique_category_name},
        )
        assert first_resp.status_code == 201

        # Segundo intento con el mismo nombre contra PostgreSQL real -> SQLSTATE 23505
        dup_resp = client.post(
            "/integration/categories",
            json={"name": unique_category_name},
        )
        assert dup_resp.status_code == 409

        detail = _assert_error_contract_without_sql_leaks(
            dup_resp.json(),
            dup_resp.text,
        )
        assert detail.startswith("Ya existe")
        assert detail == "Ya existe una categoría con ese nombre"

        # Verificación directa en capa de servicio / sesión con inspección de SQLSTATE
        with pytest.raises(ConflictError) as exc_info:
            with handle_db_exceptions(db_session):
                db_session.add(CategoryModel(name=unique_category_name))
                db_session.flush()

        err = exc_info.value
        assert err.error_code == "UNIQUE_VIOLATION"
        assert err.message == "Ya existe una categoría con ese nombre"
        assert isinstance(err.internal_details, dict)
        assert err.internal_details.get("sqlstate") == PG_UNIQUE_VIOLATION
    finally:
        db_session.rollback()
        db_session.query(CategoryModel).filter(
            CategoryModel.name == unique_category_name
        ).delete()
        db_session.commit()


def test_sqlstate_23503_foreign_key_violation_translates_to_409_without_sql_leak(
    client: TestClient,
    db_session: Session,
) -> None:
    """b. SQLSTATE 23503 (Foreign Key Violation): crear plato con category_id inexistente -> 409 Conflict."""
    non_existent_category_id = 999_999_999

    resp = client.post(
        "/integration/dishes",
        json={
            "name": f"Plato_FK_{uuid.uuid4().hex[:8]}",
            "description": "Plato de prueba para violación de llave foránea",
            "price": 14.50,
            "category_id": non_existent_category_id,
            "is_available": True,
        },
    )

    assert resp.status_code == 409
    detail = _assert_error_contract_without_sql_leaks(resp.json(), resp.text)
    assert detail == "La categoría asociada no existe o no está disponible"

    # Verificación directa sobre la sesión PostgreSQL comprobando SQLSTATE 23503 y constraint_name
    with pytest.raises(ConflictError) as exc_info:
        with handle_db_exceptions(db_session):
            invalid_dish = DishModel(
                name=f"Plato_FK_Direct_{uuid.uuid4().hex[:8]}",
                description="Prueba directa FK",
                price=11.00,
                category_id=non_existent_category_id,
                is_available=True,
            )
            db_session.add(invalid_dish)
            db_session.flush()

    err = exc_info.value
    assert err.error_code == "FOREIGN_KEY_VIOLATION"
    assert err.message == "La categoría asociada no existe o no está disponible"
    assert isinstance(err.internal_details, dict)
    assert err.internal_details.get("sqlstate") == PG_FOREIGN_KEY_VIOLATION
    assert err.internal_details.get("constraint_name") == "dishes_category_id_fkey"


def test_session_rollback_on_sync_and_async_handlers_prevents_pending_rollback_error(
    db_session: Session,
) -> None:
    """c. Verifica que handle_db_exceptions y handle_async_db_exceptions ejecuten rollback() y permitan reutilizar la sesión."""
    temp_cat_1 = f"Rollback_Cat1_{uuid.uuid4().hex[:8]}"
    temp_cat_2 = f"Rollback_Cat2_{uuid.uuid4().hex[:8]}"

    try:
        cat1 = CategoryModel(name=temp_cat_1)
        db_session.add(cat1)
        db_session.commit()

        # 1. Provocar SQLSTATE 23505 en la misma sesión PostgreSQL
        with pytest.raises(ConflictError):
            with handle_db_exceptions(db_session):
                db_session.add(CategoryModel(name=temp_cat_1))
                db_session.flush()

        # 2. La sesión NO debe estar en estado inválido (PendingRollbackError)
        # Ejecutamos una consulta e insertamos un nuevo registro en la misma sesión
        check_val = db_session.execute(text("SELECT 1")).scalar_one()
        assert check_val == 1

        cat2 = CategoryModel(name=temp_cat_2)
        db_session.add(cat2)
        db_session.commit()

        saved_names = set(
            db_session.scalars(
                select(CategoryModel.name).where(
                    CategoryModel.name.in_([temp_cat_1, temp_cat_2])
                )
            )
        )
        assert saved_names == {temp_cat_1, temp_cat_2}

        # 3. Provocar SQLSTATE 23503 (FK Violation) y verificar recuperación inmediata de la misma sesión
        with pytest.raises(ConflictError):
            with handle_db_exceptions(db_session):
                db_session.add(
                    DishModel(
                        name="Plato_Invalido",
                        price=9.99,
                        category_id=888_888_888,
                        is_available=True,
                    )
                )
                db_session.flush()

        active_count = db_session.query(CategoryModel).filter(
            CategoryModel.name.in_([temp_cat_1, temp_cat_2])
        ).count()
        assert active_count == 2

        # 4. Verificar handle_async_db_exceptions invocando await session.rollback()
        class _AsyncSessionAdapter:
            def __init__(self, sync_sess: Session) -> None:
                self._sync_sess = sync_sess
                self.rollback = AsyncMock(side_effect=self._do_rollback)

            async def _do_rollback(self) -> None:
                self._sync_sess.rollback()

        async_adapter = _AsyncSessionAdapter(db_session)

        async def _trigger_async_fk_violation() -> None:
            async with handle_async_db_exceptions(async_adapter):
                db_session.add(
                    DishModel(
                        name="Plato_Async_Invalido",
                        price=12.00,
                        category_id=777_777_777,
                        is_available=True,
                    )
                )
                db_session.flush()

        with pytest.raises(ConflictError) as async_exc_info:
            asyncio.run(_trigger_async_fk_violation())

        assert async_exc_info.value.error_code == "FOREIGN_KEY_VIOLATION"
        async_adapter.rollback.assert_awaited_once()

        # La sesión subyacente sigue limpia tras el rollback asíncrono
        assert db_session.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        db_session.rollback()
        db_session.query(CategoryModel).filter(
            CategoryModel.name.in_([temp_cat_1, temp_cat_2])
        ).delete(synchronize_session=False)
        db_session.commit()


def test_create_app_lifespan_reference_data_and_dev_endpoints(
    db_session: Session,
) -> None:
    """d. Verifica que create_app() preserve el lifespan de dev, datos de referencia, favicon, health y routers."""
    application = create_app()
    with TestClient(application, raise_server_exceptions=False) as app_client:
        # 1. Endpoints de estado y estáticos de dev
        health_resp = app_client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json() == {"status": "ok"}
        assert "X-Request-ID" in health_resp.headers

        db_health_resp = app_client.get("/health/db")
        assert db_health_resp.status_code == 200
        assert db_health_resp.json() == {"message": "Conexión a la base de datos exitosa"}

        favicon_resp = app_client.get("/favicon.ico")
        assert favicon_resp.status_code in {200, 204}
        assert "X-Request-ID" in favicon_resp.headers

        docs_favicon_resp = app_client.get("/docs/favicon.ico")
        assert docs_favicon_resp.status_code in {200, 204}
        assert "X-Request-ID" in docs_favicon_resp.headers

        # 2. Verificar que lifespan cargó/verificó categorías base y alérgenos UE
        categories_resp = app_client.get("/categories/")
        assert categories_resp.status_code == 200
        category_names = {item["name"] for item in categories_resp.json()}
        assert set(BASE_CATEGORIES).issubset(category_names)

        allergens_resp = app_client.get("/allergens/")
        assert allergens_resp.status_code == 200
        allergen_names = {item["name"] for item in allergens_resp.json()}
        assert set(EU_ALLERGENS).issubset(allergen_names)

        # 3. Verificar manejo de errores HTTP 404 en rutas reales de dev con X-Request-ID
        not_found_dish = app_client.get(
            "/dishes/999999999",
            headers={"X-Request-ID": "trace-dev-404"},
        )
        assert not_found_dish.status_code == 404
        assert not_found_dish.headers.get("X-Request-ID") == "trace-dev-404"
        assert not_found_dish.json() == {"detail": "Plato no encontrado"}
