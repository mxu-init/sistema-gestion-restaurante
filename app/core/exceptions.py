"""Jerarquía pura de excepciones de dominio (agnóstica al transporte HTTP).

Ninguna clase en este módulo importa ni hereda de FastAPI o Starlette.
"""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Excepción base de dominio para toda la aplicación."""

    default_message: str = "Ha ocurrido un error en la aplicación"
    default_error_code: str = "APP_ERROR"

    def __init__(
        self,
        message: str | None = None,
        *,
        error_code: str | None = None,
        internal_details: dict[str, Any] | str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message: str = message if message is not None else self.default_message
        self.error_code: str = (
            error_code if error_code is not None else self.default_error_code
        )
        self.internal_details: dict[str, Any] | str | None = internal_details
        self.headers: dict[str, str] | None = headers
        super().__init__(self.message)

    @property
    def detail(self) -> str:
        """Alias de solo lectura para compatibilidad con manejadores."""
        return self.message


class NotFoundError(AppError):
    """El recurso solicitado no existe (mapeado a HTTP 404)."""

    default_message: str = "El recurso solicitado no fue encontrado"
    default_error_code: str = "NOT_FOUND"


class ConflictError(AppError):
    """Conflicto de estado o violación de integridad/unicidad (mapeado a HTTP 409)."""

    default_message: str = "Conflicto con el estado actual del recurso"
    default_error_code: str = "CONFLICT"


class PermissionDeniedError(AppError):
    """Permiso denegado para la operación solicitada (mapeado a HTTP 403)."""

    default_message: str = "No tiene permisos para realizar esta acción"
    default_error_code: str = "PERMISSION_DENIED"


class DomainValidationError(AppError):
    """Violación de una regla semántica o de negocio del dominio (mapeado a HTTP 422)."""

    default_message: str = (
        "Los datos proporcionados no cumplen las reglas de validación"
    )
    default_error_code: str = "DOMAIN_VALIDATION_ERROR"


class DatabaseRetryableError(AppError):
    """Conflicto transitorio de concurrencia en base de datos (SQLSTATE 40001 / 40P01)."""

    default_message: str = (
        "Conflicto temporal de concurrencia, por favor intente nuevamente"
    )
    default_error_code: str = "DATABASE_RETRYABLE_ERROR"


class InfrastructureError(AppError):
    """Fallo de infraestructura o error inesperado (mapeado a HTTP 500)."""

    default_message: str = "Error interno del servidor"
    default_error_code: str = "INFRASTRUCTURE_ERROR"


__all__ = [
    "AppError",
    "ConflictError",
    "DatabaseRetryableError",
    "DomainValidationError",
    "InfrastructureError",
    "NotFoundError",
    "PermissionDeniedError",
]
