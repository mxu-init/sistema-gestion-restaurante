"""Suite de pruebas unitarias y de contrato para el manejo centralizado de excepciones (SGR-49)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
import pytest
from sqlalchemy import Column, Integer, String, create_engine, select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_translations import (
    PG_DEADLOCK_DETECTED,
    PG_FOREIGN_KEY_VIOLATION,
    PG_UNIQUE_VIOLATION,
    extract_constraint_name,
    extract_field_name,
    extract_sqlstate,
    handle_async_db_exceptions,
    handle_db_exceptions,
    translate_sqlalchemy_error,
)
from app.core.exceptions import (
    AppError,
    ConflictError,
    DatabaseRetryableError,
    DomainValidationError,
    InfrastructureError,
    NotFoundError,
    PermissionDeniedError,
)
from app.core.handlers import register_exception_handlers
from app.core.logging_config import (
    CorrelationIdMiddleware,
    REDACTED_VALUE,
    redact_sensitive_data,
)
from app.main import configure_openapi
from app.schemas.errors import COMMON_ERROR_RESPONSES


class _DireccionSchema(BaseModel):
    calle: str = Field(..., min_length=3)
    codigo_postal: str = Field(..., min_length=5, max_length=10)


class _UsuarioSchema(BaseModel):
    nombre: str = Field(..., min_length=2)
    direccion: _DireccionSchema


class _RegistroPayload(BaseModel):
    nombre: str = Field(..., min_length=2)
    usuario: _UsuarioSchema | None = None


@pytest.fixture()
def test_app() -> FastAPI:
    """Construye una aplicación FastAPI aislada con todos los manejadores y override OpenAPI."""
    app = FastAPI(
        title="SGR Test API",
        version="1.0.0",
        responses=COMMON_ERROR_RESPONSES,
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(app)

    @app.get("/test/not-found")
    async def route_not_found() -> dict[str, str]:
        raise NotFoundError("La mesa solicitada no fue encontrada")

    @app.post("/test/conflict")
    async def route_conflict() -> dict[str, str]:
        raise ConflictError("Ya existe una reserva activa para esta mesa")

    @app.get("/test/forbidden")
    async def route_forbidden() -> dict[str, str]:
        raise PermissionDeniedError("No tiene permisos para modificar el menú")

    @app.post("/test/domain-validation")
    async def route_domain_validation() -> dict[str, str]:
        raise DomainValidationError(
            "La fecha de reserva debe ser posterior a la hora actual"
        )

    @app.post("/test/validation")
    async def route_validation(payload: _RegistroPayload) -> dict[str, str]:
        return {"nombre": payload.nombre}

    @app.get("/test/crash")
    async def route_crash() -> dict[str, str]:
        raise RuntimeError(
            "Database failure at postgresql+psycopg://admin:supersecret@db:5432/prod"
        )

    @app.get("/test/unauthorized")
    async def route_unauthorized() -> dict[str, str]:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )

    configure_openapi(app)
    return app


@pytest.fixture()
def client(test_app: FastAPI) -> TestClient:
    """Cliente de pruebas sin relanzar excepciones del servidor para verificar HTTP 500."""
    return TestClient(test_app, raise_server_exceptions=False)


def _assert_strict_spanish_contract(
    response_json: dict[str, object],
) -> str:
    """Verifica que el cuerpo JSON contenga única y exclusivamente la clave `detail`."""
    assert list(response_json.keys()) == ["detail"]
    detail = response_json["detail"]
    assert isinstance(detail, str)
    assert len(detail.strip()) > 0
    return detail


def test_not_found_error_returns_404_spanish_detail(client: TestClient) -> None:
    """Verifica que NotFoundError devuelva HTTP 404 con contrato único en español."""
    response = client.get("/test/not-found")

    assert response.status_code == 404
    detail = _assert_strict_spanish_contract(response.json())
    assert detail == "La mesa solicitada no fue encontrada"
    assert "X-Request-ID" in response.headers


def test_conflict_error_returns_409_spanish_detail(client: TestClient) -> None:
    """Verifica que ConflictError devuelva HTTP 409 con contrato único en español."""
    response = client.post("/test/conflict")

    assert response.status_code == 409
    detail = _assert_strict_spanish_contract(response.json())
    assert detail == "Ya existe una reserva activa para esta mesa"


def test_permission_denied_error_returns_403_spanish_detail(
    client: TestClient,
) -> None:
    """Verifica que PermissionDeniedError devuelva HTTP 403 con contrato único en español."""
    response = client.get("/test/forbidden")

    assert response.status_code == 403
    detail = _assert_strict_spanish_contract(response.json())
    assert detail == "No tiene permisos para modificar el menú"


def test_validation_missing_field_exact_prompt_contract(
    client: TestClient,
) -> None:
    """Verifica el mensaje exacto cuando falta un campo obligatorio en Pydantic v2."""
    response = client.post("/test/validation", json={})

    assert response.status_code == 422
    detail = _assert_strict_spanish_contract(response.json())
    assert detail == "Error en el campo 'nombre': El campo es obligatorio"


def test_validation_nested_object_extracts_leaf_field_without_schema_leak(
    client: TestClient,
) -> None:
    """Verifica que un error en un objeto anidado extraiga solo el campo hoja sin filtrar rutas ni esquemas."""
    payload = {
        "nombre": "Carlos",
        "usuario": {
            "nombre": "Carlos",
            "direccion": {
                "calle": "Gran Vía 12",
                "codigo_postal": "12",
            },
        },
    }
    response = client.post("/test/validation", json=payload)

    assert response.status_code == 422
    detail = _assert_strict_spanish_contract(response.json())
    assert "Error en el campo 'codigo_postal':" in detail
    assert "body" not in detail
    assert "usuario" not in detail
    assert "direccion" not in detail
    assert "_DireccionSchema" not in detail
    assert "_UsuarioSchema" not in detail
    assert "_RegistroPayload" not in detail
    assert (
        extract_field_name(("body", "usuario", "direccion", "codigo_postal"))
        == "codigo_postal"
    )


def test_unexpected_exception_returns_generic_spanish_500_without_traceback(
    client: TestClient,
) -> None:
    """Verifica que una excepción no controlada devuelva HTTP 500 genérico sin filtrar trazas ni DSNs."""
    response = client.get("/test/crash")

    assert response.status_code == 500
    detail = _assert_strict_spanish_contract(response.json())
    assert detail == "Error interno del servidor"
    raw_body = response.text.lower()
    assert "traceback" not in raw_body
    assert "runtimeerror" not in raw_body
    assert "supersecret" not in raw_body
    assert "postgresql" not in raw_body


def test_openapi_schema_uses_error_response_for_422_and_removes_default_validation_schema(
    test_app: FastAPI,
) -> None:
    """Verifica que OpenAPI reemplace HTTPValidationError por ErrorResponse en todas las respuestas 422."""
    schema = test_app.openapi()
    components_schemas = schema["components"]["schemas"]

    assert "ErrorResponse" in components_schemas
    assert "HTTPValidationError" not in components_schemas
    assert "ValidationError" not in components_schemas

    error_schema = components_schemas["ErrorResponse"]
    assert set(error_schema["properties"].keys()) == {"detail"}
    assert error_schema.get("additionalProperties") is False

    validation_422 = schema["paths"]["/test/validation"]["post"]["responses"]["422"]
    ref = validation_422["content"]["application/json"]["schema"]["$ref"]
    assert ref == "#/components/schemas/ErrorResponse"


def test_session_rollback_prevents_pending_rollback_error_on_reuse() -> None:
    """Verifica que handle_db_exceptions ejecute session.rollback() y permita reutilizar la sesión."""

    class _TestBase(DeclarativeBase):
        pass

    class _CategoriaItem(_TestBase):
        __tablename__ = "categorias_test"
        id = Column(Integer, primary_key=True, autoincrement=True)
        nombre = Column(String(80), unique=True, nullable=False)

    engine = create_engine("sqlite:///:memory:")
    _TestBase.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as session:
        assert isinstance(session, Session)
        primera = _CategoriaItem(nombre="Postres")
        session.add(primera)
        session.commit()

        with pytest.raises(ConflictError) as exc_info:
            with handle_db_exceptions(session):
                duplicada = _CategoriaItem(nombre="Postres")
                session.add(duplicada)
                session.flush()

        assert exc_info.value.message

        # La sesión debe seguir siendo utilizable sin lanzar PendingRollbackError
        scalar_check = session.execute(text("SELECT 1")).scalar_one()
        assert scalar_check == 1

        segunda = _CategoriaItem(nombre="Bebidas")
        session.add(segunda)
        session.commit()

        nombres = list(
            session.scalars(
                select(_CategoriaItem.nombre).order_by(_CategoriaItem.id)
            )
        )
        assert nombres == ["Postres", "Bebidas"]


def test_domain_exceptions_are_transport_agnostic() -> None:
    """Garantiza que ninguna excepción de dominio herede de HTTPException de FastAPI/Starlette."""
    for exc_cls in (
        AppError,
        NotFoundError,
        ConflictError,
        PermissionDeniedError,
        DomainValidationError,
        DatabaseRetryableError,
        InfrastructureError,
    ):
        assert issubclass(exc_cls, Exception)
        assert not issubclass(exc_cls, StarletteHTTPException)
        assert not issubclass(exc_cls, HTTPException)


def test_postgresql_sqlstate_and_constraint_extraction_psycopg_and_asyncpg() -> None:
    """Verifica la extracción dual de SQLSTATE y constraint_name para psycopg v3 y asyncpg."""
    psycopg_orig = SimpleNamespace(
        sqlstate=PG_UNIQUE_VIOLATION,
        diag=SimpleNamespace(constraint_name="uq_categories_name"),
    )
    psycopg_exc = IntegrityError("INSERT INTO categories ...", {}, psycopg_orig)

    assert extract_sqlstate(psycopg_exc) == PG_UNIQUE_VIOLATION
    assert extract_constraint_name(psycopg_exc) == "uq_categories_name"
    translated_unique = translate_sqlalchemy_error(psycopg_exc)
    assert isinstance(translated_unique, ConflictError)
    assert translated_unique.message == "Ya existe una categoría con ese nombre"

    asyncpg_cause = SimpleNamespace(
        sqlstate=PG_FOREIGN_KEY_VIOLATION,
        constraint_name="dishes_category_id_fkey",
    )
    asyncpg_orig = SimpleNamespace(__cause__=asyncpg_cause)
    asyncpg_exc = IntegrityError("INSERT INTO dishes ...", {}, asyncpg_orig)

    assert extract_sqlstate(asyncpg_exc) == PG_FOREIGN_KEY_VIOLATION
    assert extract_constraint_name(asyncpg_exc) == "dishes_category_id_fkey"
    translated_fk = translate_sqlalchemy_error(asyncpg_exc)
    assert isinstance(translated_fk, ConflictError)
    assert (
        translated_fk.message
        == "La categoría asociada no existe o no está disponible"
    )

    deadlock_orig = SimpleNamespace(sqlstate=PG_DEADLOCK_DETECTED, diag=None)
    deadlock_exc = OperationalError("UPDATE tables ...", {}, deadlock_orig)
    translated_deadlock = translate_sqlalchemy_error(deadlock_exc)
    assert isinstance(translated_deadlock, DatabaseRetryableError)


def test_async_session_rollback_and_sensitive_redaction(client: TestClient) -> None:
    """Verifica rollback asíncrono, preservación de WWW-Authenticate, X-Request-ID y sanitización."""
    mock_async_session = SimpleNamespace(rollback=AsyncMock())

    async def _run_async_failure() -> None:
        async with handle_async_db_exceptions(mock_async_session):
            orig = SimpleNamespace(
                sqlstate=PG_UNIQUE_VIOLATION,
                diag=SimpleNamespace(constraint_name="uq_users_email"),
            )
            raise IntegrityError("INSERT INTO users ...", {}, orig)

    with pytest.raises(ConflictError):
        asyncio.run(_run_async_failure())

    mock_async_session.rollback.assert_awaited_once()

    resp = client.get(
        "/test/unauthorized",
        headers={"X-Request-ID": "req-corr-999"},
    )
    assert resp.status_code == 401
    assert resp.headers.get("WWW-Authenticate") == "Bearer"
    assert resp.headers.get("X-Request-ID") == "req-corr-999"
    assert _assert_strict_spanish_contract(resp.json()) == "No autenticado"

    sanitized = redact_sensitive_data(
        {
            "usuario": "admin",
            "password": "my_secret_password",
            "api_key": "12345-abcde",
            "nested": {
                "dsn": "postgresql+psycopg://user:pass@localhost:5432/sgr_db",
                "nota": "Conectado a postgresql+psycopg://user:pass@localhost:5432/sgr_db con Bearer eyJhbGciOi",
            },
        }
    )
    assert sanitized["usuario"] == "admin"
    assert sanitized["password"] == REDACTED_VALUE
    assert sanitized["api_key"] == REDACTED_VALUE
    assert sanitized["nested"]["dsn"] == REDACTED_VALUE
    assert "pass@localhost" not in sanitized["nested"]["nota"]
    assert REDACTED_VALUE in sanitized["nested"]["nota"]
