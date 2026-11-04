"""Esquema único de respuesta de error y catálogo OpenAPI 3.1."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """Contrato estricto y único para todas las respuestas de error de la API."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "detail": "Mensaje descriptivo del error en español",
            }
        },
    )

    detail: str = Field(
        ...,
        description="Descripción clara y legible del error en español.",
        examples=["El recurso solicitado no fue encontrado"],
    )


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "model": ErrorResponse,
        "description": "Solicitud inválida",
    },
    401: {
        "model": ErrorResponse,
        "description": "No autenticado",
    },
    403: {
        "model": ErrorResponse,
        "description": "Permiso denegado",
    },
    404: {
        "model": ErrorResponse,
        "description": "Recurso no encontrado",
    },
    409: {
        "model": ErrorResponse,
        "description": "Conflicto con el estado actual del recurso",
    },
    422: {
        "model": ErrorResponse,
        "description": "Error de validación de datos o regla de dominio",
    },
    500: {
        "model": ErrorResponse,
        "description": "Error interno del servidor",
    },
}

__all__ = [
    "COMMON_ERROR_RESPONSES",
    "ErrorResponse",
]
