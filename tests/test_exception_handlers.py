"""Pruebas para el manejo centralizado de errores en español (SGR-49 / SGR-10)."""

import logging
from unittest.mock import MagicMock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
import pytest

from app.core.database_connection import get_db
from app.core.exceptions import (
    PYDANTIC_SPANISH_MESSAGES,
    AppError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    extract_field_name,
    format_validation_reason,
    register_exception_handlers,
)
from app.main import app as main_app
from app.schemas.errors import COMMON_ERROR_RESPONSES
from app.services import menu_service


class _AddressInput(BaseModel):
    postal_code: str = Field(..., min_length=5)


class _ReservationInput(BaseModel):
    nombre: str = Field(..., min_length=2)
    comensales: int = Field(..., gt=0, le=20)
    direccion: _AddressInput | None = None


@pytest.fixture()
def client() -> TestClient:
    """Aplicación FastAPI de prueba con los manejadores globales registrados."""
    test_app = FastAPI(responses=COMMON_ERROR_RESPONSES)
    register_exception_handlers(test_app)

    @test_app.get("/test/not-found")
    def raise_not_found():
        raise NotFoundError("Plato no encontrado")

    @test_app.post("/test/conflict")
    def raise_conflict():
        raise ConflictError("Ya existe una categoría con ese nombre")

    @test_app.get("/test/forbidden")
    def raise_forbidden():
        raise PermissionDeniedError("No tiene permisos para eliminar este plato")

    @test_app.get("/test/unauthorized")
    def raise_unauthorized():
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @test_app.post("/test/validation")
    def validate_body(payload: _ReservationInput):
        return payload.model_dump()

    @test_app.get("/test/crash")
    def raise_unhandled():
        raise RuntimeError("Fallo interno en base de datos: secret_password_123")

    return TestClient(test_app, raise_server_exceptions=False)


def test_domain_errors_404_409_403_return_spanish_detail(client: TestClient) -> None:
    """AC-1 & AC-2: 404, 409 y 403 devuelven JSON {'detail': '...'} en español."""
    r_404 = client.get("/test/not-found")
    assert r_404.status_code == 404
    assert r_404.json() == {"detail": "Plato no encontrado"}

    r_409 = client.post("/test/conflict")
    assert r_409.status_code == 409
    assert r_409.json() == {"detail": "Ya existe una categoría con ese nombre"}

    r_403 = client.get("/test/forbidden")
    assert r_403.status_code == 403
    assert r_403.json() == {"detail": "No tiene permisos para eliminar este plato"}


def test_http_401_translates_default_message_and_preserves_headers(
    client: TestClient,
) -> None:
    """RN-GEN-04: 401 devuelve mensaje en español y conserva WWW-Authenticate."""
    resp = client.get("/test/unauthorized")
    assert resp.status_code == 401
    assert resp.json() == {"detail": "No autenticado"}
    assert resp.headers.get("WWW-Authenticate") == "Bearer"


def test_validation_error_422_identifies_missing_and_nested_fields(
    client: TestClient,
) -> None:
    """AC-2 & AC-3: Los errores 422 usan {'detail': '...'} e indican el campo erróneo."""
    r_missing = client.post("/test/validation", json={"comensales": 4})
    assert r_missing.status_code == 422
    assert r_missing.json() == {
        "detail": "Error en el campo 'nombre': El campo es obligatorio"
    }

    r_nested = client.post(
        "/test/validation",
        json={
            "nombre": "Ana",
            "comensales": 4,
            "direccion": {"postal_code": "12"},
        },
    )
    assert r_nested.status_code == 422
    assert r_nested.json() == {
        "detail": "Error en el campo 'postal_code': El texto debe tener al menos 5 caracteres"
    }
    assert extract_field_name(("body", "direccion", "postal_code")) == "postal_code"


def test_unhandled_exception_returns_generic_500_and_logs_error(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """AC-4: Un error no controlado devuelve 500 genérico sin filtrar detalles internos."""
    with caplog.at_level(logging.ERROR):
        resp = client.get("/test/crash")

    assert resp.status_code == 500
    assert resp.json() == {"detail": "Error interno del servidor"}
    assert "secret_password_123" not in resp.text
    assert "RuntimeError" not in resp.text
    assert any("Excepción no controlada" in rec.message for rec in caplog.records)


def test_all_pydantic_spanish_messages_mappings() -> None:
    """Verifica que las 53 entradas de PYDANTIC_SPANISH_MESSAGES formateen correctamente."""
    assert len(PYDANTIC_SPANISH_MESSAGES) == 53
    sample_ctx = {
        "min_length": 3,
        "max_length": 50,
        "gt": 0,
        "ge": 1,
        "lt": 100,
        "le": 20,
        "multiple_of": 5,
    }
    for error_type in PYDANTIC_SPANISH_MESSAGES:
        reason = format_validation_reason(error_type, sample_ctx)
        assert isinstance(reason, str) and len(reason) > 0
        assert "{" not in reason

    # Subtipos con prefijo (ej. string_too_short en variantes de Pydantic) y contexto vacío
    assert (
        format_validation_reason("int_parsing_extra")
        == PYDANTIC_SPANISH_MESSAGES["int_parsing"]
    )
    assert (
        format_validation_reason("string_too_short", {})
        == "El valor proporcionado no es válido"
    )


def test_menu_service_compatibility_and_swagger_responses() -> None:
    """Verifica compatibilidad con menu_service.py, endpoints /menus y respuestas Swagger."""
    mock_db = MagicMock()
    mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
        None
    )

    with pytest.raises(NotFoundError) as exc_info:
        menu_service.fetch_menu_by_id(mock_db, 999)
    assert isinstance(exc_info.value, AppError)
    assert exc_info.value.message == "El menú no existe"
    assert exc_info.value.status_code == 404

    deleted_menu = MagicMock(deleted_at="2026-11-11T00:00:00Z")
    mock_db.query.return_value.filter.return_value.first.return_value = deleted_menu
    with pytest.raises(ConflictError) as conflict_info:
        menu_service.soft_delete_menu(mock_db, 1)
    assert conflict_info.value.message == "El menú ya ha sido eliminado"
    assert conflict_info.value.status_code == 409

    # Verificar endpoints reales de /menus (404, 409 y 422) en main_app
    app_client = TestClient(main_app, raise_server_exceptions=False)
    main_app.dependency_overrides[get_db] = lambda: mock_db
    try:
        mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = (
            None
        )
        r_menu_404 = app_client.get("/menus/999")
        assert r_menu_404.status_code == 404
        assert r_menu_404.json() == {"detail": "El menú no existe"}

        mock_db.query.return_value.filter.return_value.first.return_value = deleted_menu
        r_menu_409 = app_client.delete("/menus/1")
        assert r_menu_409.status_code == 409
        assert r_menu_409.json() == {"detail": "El menú ya ha sido eliminado"}

        invalid_menu_resp = app_client.post("/menus", json={})
        assert invalid_menu_resp.status_code == 422
        assert (
            "Error en el campo 'name': El campo es obligatorio"
            in invalid_menu_resp.json()["detail"]
        )
    finally:
        main_app.dependency_overrides.clear()

    openapi_schema = main_app.openapi()
    assert "/menus" in openapi_schema["paths"]
    assert "ErrorResponse" in openapi_schema["components"]["schemas"]
