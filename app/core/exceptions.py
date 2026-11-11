"""Excepciones de dominio y manejadores globales de errores en español (SGR-49)."""

from collections.abc import Mapping, Sequence
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Excepción base para errores de negocio de la aplicación."""

    default_message: str = "Ha ocurrido un error en la aplicación"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None) -> None:
        self.message: str = message if message is not None else self.default_message
        super().__init__(self.message)


class NotFoundError(AppError):
    """Recurso inexistente (HTTP 404)."""

    default_message: str = "El recurso solicitado no fue encontrado"
    status_code: int = status.HTTP_404_NOT_FOUND


class ConflictError(AppError):
    """Conflicto con el estado actual del recurso (HTTP 409)."""

    default_message: str = "Conflicto con el estado actual del recurso"
    status_code: int = status.HTTP_409_CONFLICT


class PermissionDeniedError(AppError):
    """Falta de permisos para realizar la operación (HTTP 403)."""

    default_message: str = "No tiene permisos para realizar esta acción"
    status_code: int = status.HTTP_403_FORBIDDEN


PYDANTIC_SPANISH_MESSAGES: dict[str, str] = {
    "missing": "El campo es obligatorio",
    "string_type": "Debe ser una cadena de texto válida",
    "string_too_short": "El texto debe tener al menos {min_length} caracteres",
    "string_too_long": "El texto no puede exceder {max_length} caracteres",
    "string_pattern_mismatch": "El formato del texto no es válido",
    "int_type": "Debe ser un número entero",
    "int_parsing": "Debe ser un número entero válido",
    "int_from_float": "Debe ser un número entero sin decimales",
    "float_type": "Debe ser un número válido",
    "float_parsing": "Debe ser un número decimal válido",
    "decimal_type": "Debe ser un valor decimal válido",
    "decimal_parsing": "Debe ser un valor decimal válido",
    "bool_type": "Debe ser un valor booleano (verdadero o falso)",
    "bool_parsing": "Debe ser un valor booleano válido",
    "greater_than": "El valor debe ser mayor que {gt}",
    "greater_than_equal": "El valor debe ser mayor o igual a {ge}",
    "less_than": "El valor debe ser menor que {lt}",
    "less_than_equal": "El valor debe ser menor o igual a {le}",
    "multiple_of": "El valor debe ser múltiplo de {multiple_of}",
    "finite_number": "El valor debe ser un número finito",
    "list_type": "Debe ser una lista válida",
    "too_short": "La colección contiene menos elementos de los requeridos",
    "too_long": "La colección excede la cantidad máxima de elementos",
    "set_type": "Debe ser un conjunto válido",
    "dict_type": "Debe ser un objeto válido",
    "model_type": "El formato del objeto no es válido",
    "model_attributes_type": "El formato del objeto no es válido",
    "json_invalid": "El cuerpo de la petición no contiene un JSON válido",
    "json_type": "El formato JSON no es válido",
    "enum": "El valor proporcionado no está dentro de las opciones permitidas",
    "literal_error": "El valor proporcionado no está dentro de las opciones permitidas",
    "date_type": "Debe ser una fecha válida",
    "date_parsing": "El formato de la fecha no es válido (YYYY-MM-DD)",
    "date_from_datetime_parsing": "El formato de la fecha no es válido",
    "date_from_datetime_inexact": "La fecha no debe incluir hora",
    "date_future": "La fecha debe estar en el futuro",
    "date_past": "La fecha debe estar en el pasado",
    "time_type": "Debe ser una hora válida",
    "time_parsing": "El formato de la hora no es válido (HH:MM:SS)",
    "datetime_type": "Debe ser una fecha y hora válida",
    "datetime_parsing": "El formato de fecha y hora no es válido",
    "datetime_from_date_parsing": "El formato de fecha y hora no es válido",
    "datetime_future": "La fecha y hora deben estar en el futuro",
    "datetime_past": "La fecha y hora deben estar en el pasado",
    "uuid_type": "Debe ser un identificador UUID válido",
    "uuid_parsing": "El formato del identificador UUID no es válido",
    "url_type": "Debe ser una URL válida",
    "url_parsing": "El formato de la URL no es válido",
    "url_scheme": "El esquema de la URL no es válido",
    "email": "El formato del correo electrónico no es válido",
    "extra_forbidden": "No se permiten campos adicionales",
    "value_error": "El valor proporcionado no es válido",
    "assertion_error": "El valor no cumple las reglas de validación",
}

HTTP_ENGLISH_TO_SPANISH: dict[str, str] = {
    "not found": "Recurso no encontrado",
    "method not allowed": "Método HTTP no permitido para esta ruta",
    "unauthorized": "No autenticado",
    "not authenticated": "No autenticado",
    "invalid authentication credentials": "Credenciales de autenticación inválidas",
    "forbidden": "No tiene permisos para realizar esta acción",
    "bad request": "Solicitud inválida",
    "conflict": "Conflicto con el estado actual del recurso",
    "unprocessable entity": "Datos de entrada inválidos",
    "unprocessable content": "Datos de entrada inválidos",
    "internal server error": "Error interno del servidor",
}


def extract_field_name(loc: Sequence[str | int]) -> str:
    """Extrae el nombre del campo hoja de la ubicación del error."""
    for item in reversed(loc):
        if isinstance(item, str) and item not in ("body", "query", "path", "header", "cookie"):
            return item
    return "cuerpo"


def format_validation_reason(
    error_type: str,
    ctx: Mapping[str, Any] | None = None,
) -> str:
    """Obtiene el mensaje en español correspondiente al tipo de error de Pydantic."""
    template = PYDANTIC_SPANISH_MESSAGES.get(error_type)
    if template is None:
        template = next(
            (
                msg
                for prefix, msg in PYDANTIC_SPANISH_MESSAGES.items()
                if error_type.startswith(prefix)
            ),
            "El valor proporcionado no es válido",
        )
    if "{" not in template:
        return template
    try:
        return template.format(**(ctx or {}))
    except (KeyError, ValueError, IndexError):
        return "El valor proporcionado no es válido"


def translate_validation_errors(errors: Sequence[Mapping[str, Any]]) -> str:
    """Convierte la lista de errores de validación (422) en un mensaje claro en español."""
    if not errors:
        return "Datos de entrada inválidos"

    messages: list[str] = []
    for err in errors:
        error_type = str(err.get("type", ""))
        if error_type == "json_invalid":
            messages.append(PYDANTIC_SPANISH_MESSAGES["json_invalid"])
            continue

        field_name = extract_field_name(err.get("loc", ()))
        ctx = err.get("ctx") if isinstance(err.get("ctx"), Mapping) else None
        reason = format_validation_reason(error_type, ctx)
        messages.append(f"Error en el campo '{field_name}': {reason}")

    return "; ".join(messages)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Manejador global para excepciones de dominio (`AppError` y subclases)."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Manejador global para `HTTPException` preservando cabeceras y mensajes en español."""
    if exc.status_code >= 500:
        detail = "Error interno del servidor"
    elif isinstance(exc.detail, str) and exc.detail.strip():
        raw = exc.detail.strip()
        detail = HTTP_ENGLISH_TO_SPANISH.get(raw.lower(), raw)
    else:
        detail = "Ha ocurrido un error al procesar la solicitud"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": detail},
        headers=exc.headers,
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Manejador global para errores de validación 422 indicando el campo erróneo."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": translate_validation_errors(exc.errors())},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Manejador global para errores no controlados (500) sin exponer detalles internos."""
    logger.exception(
        "Excepción no controlada en %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores centralizados de excepciones en la aplicación FastAPI."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)
