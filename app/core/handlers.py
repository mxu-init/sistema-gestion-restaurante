"""Manejadores globales de excepciones para FastAPI / Starlette."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_translations import (
    translate_sqlalchemy_error,
    translate_validation_errors,
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
from app.core.logging_config import (
    configure_logging,
    get_correlation_id,
    redact_sensitive_data,
)
from app.schemas.errors import ErrorResponse

logger = configure_logging()

HTTP_422_STATUS = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)

DOMAIN_EXCEPTION_STATUS_MAP: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
    DomainValidationError: HTTP_422_STATUS,
    DatabaseRetryableError: status.HTTP_503_SERVICE_UNAVAILABLE,
    InfrastructureError: status.HTTP_500_INTERNAL_SERVER_ERROR,
    AppError: status.HTTP_400_BAD_REQUEST,
}

_DEFAULT_HTTP_ENGLISH_TO_SPANISH: dict[str, str] = {
    "not found": "Recurso no encontrado",
    "method not allowed": "Método HTTP no permitido para esta ruta",
    "unauthorized": "No autenticado",
    "not authenticated": "No autenticado",
    "invalid authentication credentials": "Credenciales de autenticación inválidas",
    "forbidden": "No tiene permisos para realizar esta acción",
    "bad request": "Solicitud inválida",
    "internal server error": "Error interno del servidor",
    "service unavailable": "Servicio temporalmente no disponible",
    "conflict": "Conflicto con el estado actual del recurso",
    "unprocessable entity": "Datos de entrada inválidos",
    "unprocessable content": "Datos de entrada inválidos",
    "too many requests": "Demasiadas solicitudes, por favor intente más tarde",
}

_DEFAULT_STATUS_SPANISH_FALLBACK: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "Solicitud inválida",
    status.HTTP_401_UNAUTHORIZED: "No autenticado",
    status.HTTP_403_FORBIDDEN: "No tiene permisos para realizar esta acción",
    status.HTTP_404_NOT_FOUND: "Recurso no encontrado",
    status.HTTP_405_METHOD_NOT_ALLOWED: "Método HTTP no permitido para esta ruta",
    status.HTTP_409_CONFLICT: "Conflicto con el estado actual del recurso",
    HTTP_422_STATUS: "Datos de entrada inválidos",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "Error interno del servidor",
    status.HTTP_503_SERVICE_UNAVAILABLE: "Servicio temporalmente no disponible",
}


def _resolve_domain_status_code(exc: AppError) -> int:
    """Resuelve el código de estado HTTP según la jerarquía de clases de AppError."""
    exc_type = type(exc)
    if exc_type in DOMAIN_EXCEPTION_STATUS_MAP:
        return DOMAIN_EXCEPTION_STATUS_MAP[exc_type]

    for cls in exc_type.__mro__:
        if issubclass(cls, AppError) and cls in DOMAIN_EXCEPTION_STATUS_MAP:
            return DOMAIN_EXCEPTION_STATUS_MAP[cls]

    return status.HTTP_400_BAD_REQUEST


def _build_response_headers(
    request: Request,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {}
    if extra_headers:
        headers.update(extra_headers)

    correlation_id = get_correlation_id() or getattr(
        getattr(request, "state", None), "correlation_id", None
    )
    if correlation_id and not any(
        k.lower() == "x-request-id" for k in headers
    ):
        headers["X-Request-ID"] = str(correlation_id)

    return headers


def _build_error_json_response(
    request: Request,
    *,
    status_code: int,
    detail: str,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(detail=detail).model_dump()
    merged_headers = _build_response_headers(request, headers)
    return JSONResponse(
        status_code=status_code,
        content=payload,
        headers=merged_headers or None,
    )


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Procesa excepciones de dominio `AppError` y las serializa al contrato único."""
    status_code = _resolve_domain_status_code(exc)
    is_internal_500 = (
        status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        or isinstance(exc, InfrastructureError)
    )

    log_context = redact_sensitive_data(
        {
            "path": request.url.path,
            "method": request.method,
            "status_code": status_code,
            "error_code": exc.error_code,
            "internal_details": exc.internal_details,
        }
    )

    if is_internal_500:
        logger.error(
            "Error de infraestructura o servidor en dominio",
            extra={"context": log_context, "error_code": exc.error_code},
        )
        detail = "Error interno del servidor"
    else:
        logger.warning(
            exc.message,
            extra={"context": log_context, "error_code": exc.error_code},
        )
        detail = exc.message

    return _build_error_json_response(
        request,
        status_code=status_code,
        detail=detail,
        headers=exc.headers,
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Intercepta `RequestValidationError` y responde con HTTP 422 en español sin filtrar `input`."""
    raw_errors = exc.errors()
    detail = translate_validation_errors(raw_errors)

    safe_error_summary = [
        {"loc": err.get("loc"), "type": err.get("type")} for err in raw_errors
    ]
    logger.warning(
        "Error de validación en la petición de entrada",
        extra={
            "context": {
                "path": request.url.path,
                "method": request.method,
                "errors": safe_error_summary,
            },
            "error_code": "REQUEST_VALIDATION_ERROR",
        },
    )

    return _build_error_json_response(
        request,
        status_code=HTTP_422_STATUS,
        detail=detail,
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Intercepta `StarletteHTTPException`, traduce mensajes por defecto y preserva cabeceras."""
    raw_detail = exc.detail
    if isinstance(raw_detail, str) and raw_detail.strip():
        normalized = raw_detail.strip().lower()
        detail = _DEFAULT_HTTP_ENGLISH_TO_SPANISH.get(
            normalized, raw_detail.strip()
        )
    else:
        detail = _DEFAULT_STATUS_SPANISH_FALLBACK.get(
            exc.status_code,
            "Ha ocurrido un error al procesar la solicitud",
        )

    if exc.status_code >= 500:
        detail = "Error interno del servidor"

    headers = dict(exc.headers) if exc.headers else None
    return _build_error_json_response(
        request,
        status_code=exc.status_code,
        detail=detail,
        headers=headers,
    )


async def sqlalchemy_exception_handler(
    request: Request,
    exc: SQLAlchemyError,
) -> JSONResponse:
    """Red de seguridad global para `SQLAlchemyError` no capturados en la capa de servicio."""
    domain_exc = translate_sqlalchemy_error(exc)
    return await app_error_handler(request, domain_exc)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Manejador de último recurso (HTTP 500) sin exponer trazas ni detalles internos."""
    logger.error(
        "Excepción no controlada capturada por el manejador global",
        exc_info=exc,
        extra={
            "context": redact_sensitive_data(
                {
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(exc).__name__,
                }
            ),
            "error_code": "UNHANDLED_EXCEPTION",
        },
    )

    return _build_error_json_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno del servidor",
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Registra todos los manejadores globales de excepciones en la instancia FastAPI."""
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(
        RequestValidationError,
        request_validation_error_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        SQLAlchemyError,
        sqlalchemy_exception_handler,  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, unhandled_exception_handler)


__all__ = [
    "DOMAIN_EXCEPTION_STATUS_MAP",
    "app_error_handler",
    "http_exception_handler",
    "register_exception_handlers",
    "request_validation_error_handler",
    "sqlalchemy_exception_handler",
    "unhandled_exception_handler",
]
