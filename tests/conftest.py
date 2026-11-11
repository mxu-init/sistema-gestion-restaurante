import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.core.database_connection import Base, get_db
from app.core.reference_data import BASE_CATEGORIES, EU_ALLERGENS
from app.models import AllergenModel, CategoryModel
from app.main import app as fastapi_app
import app.models  # Ensure all SQLAlchemy models are registered


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return test_engine


@pytest.fixture(scope="function")
def test_db(engine):
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Seed base categories and allergens
    for category_name in BASE_CATEGORIES:
        db.add(CategoryModel(name=category_name))
    for allergen_name in EU_ALLERGENS:
        db.add(AllergenModel(name=allergen_name))
    db.commit()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(fastapi_app)

    yield test_client

    fastapi_app.dependency_overrides.clear()

