"""Rutas de demostración e integración de la arquitectura de manejo de excepciones."""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.exceptions import (
    ConflictError,
    DomainValidationError,
    InfrastructureError,
    NotFoundError,
    PermissionDeniedError,
)
from app.schemas.errors import COMMON_ERROR_RESPONSES

router = APIRouter(
    prefix="/errores-demo",
    tags=["Contratos de Error"],
    responses=COMMON_ERROR_RESPONSES,
)


class DireccionDemoSchema(BaseModel):
    """Esquema anidado para validación de dirección postal."""

    model_config = ConfigDict(extra="forbid")

    calle: str = Field(..., min_length=2, max_length=120)
    codigo_postal: str = Field(..., min_length=4, max_length=10)


class UsuarioDemoSchema(BaseModel):
    """Esquema anidado de usuario para pruebas de extracción de campo hoja."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=80)
    direccion: DireccionDemoSchema


class ReservaDemoRequest(BaseModel):
    """Esquema de entrada para validación de reservas y objetos anidados."""

    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(..., min_length=1, max_length=100)
    comensales: int = Field(..., gt=0, le=20)
    usuario: UsuarioDemoSchema | None = None


@router.post(
    "/validacion",
    status_code=status.HTTP_201_CREATED,
    summary="Validar entrada estructurada y objetos anidados",
)
async def validar_reserva_demo(payload: ReservaDemoRequest) -> dict[str, object]:
    """Valida el cuerpo de entrada y las reglas semánticas de dominio."""
    if payload.comensales > 12:
        raise DomainValidationError(
            "Las reservas de más de 12 comensales requieren confirmación telefónica"
        )
    return {
        "nombre": payload.nombre,
        "comensales": payload.comensales,
    }


@router.get(
    "/no-encontrado/{recurso_id}",
    summary="Simular error 404 de dominio (NotFoundError)",
)
async def demo_no_encontrado(recurso_id: int) -> dict[str, int]:
    """Lanza `NotFoundError` puro de dominio."""
    raise NotFoundError(f"El recurso con identificador {recurso_id} no fue encontrado")


@router.post(
    "/conflicto",
    summary="Simular error 409 de dominio (ConflictError)",
)
async def demo_conflicto() -> dict[str, str]:
    """Lanza `ConflictError` puro de dominio."""
    raise ConflictError("Ya existe una reserva activa en la misma franja horaria")


@router.get(
    "/permiso-denegado",
    summary="Simular error 403 de dominio (PermissionDeniedError)",
)
async def demo_permiso_denegado() -> dict[str, str]:
    """Lanza `PermissionDeniedError` puro de dominio."""
    raise PermissionDeniedError("No tiene permisos para realizar esta acción")


@router.get(
    "/error-infraestructura",
    summary="Simular error 500 de infraestructura (InfrastructureError)",
)
async def demo_error_infraestructura() -> dict[str, str]:
    """Lanza `InfrastructureError` con detalles internos que no se filtran al cliente."""
    raise InfrastructureError(
        "Fallo de conexión con el nodo primario",
        internal_details={"dsn": "postgresql+psycopg://admin:secret@db:5432/sgr"},
    )
