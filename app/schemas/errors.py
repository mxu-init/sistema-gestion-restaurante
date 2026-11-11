"""Esquema común de respuesta de error para la API y documentación Swagger."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Formato JSON único para todas las respuestas de error."""

    detail: str = Field(
        ...,
        description="Mensaje claro del error en español.",
        examples=["Recurso no encontrado"],
    )


COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    401: {"model": ErrorResponse, "description": "No autenticado"},
    403: {"model": ErrorResponse, "description": "Permiso denegado"},
    404: {"model": ErrorResponse, "description": "Recurso no encontrado"},
    409: {"model": ErrorResponse, "description": "Conflicto con el estado actual"},
    422: {"model": ErrorResponse, "description": "Error de validación de datos"},
    500: {"model": ErrorResponse, "description": "Error interno del servidor"},
}
