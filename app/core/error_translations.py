"""Traductores de errores de validación (Pydantic v2) y base de datos (SQLAlchemy / PostgreSQL).

Incluye extracción segura del campo hoja, mapeo de códigos SQLSTATE para psycopg v3
y asyncpg, y gestores de contexto con rollback garantizado de sesión.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Mapping, Sequence
from contextlib import asynccontextmanager, contextmanager
import re
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import (
    AppError,
    ConflictError,
    DatabaseRetryableError,
    DomainValidationError,
    InfrastructureError,
)

# Códigos estándar SQLSTATE de PostgreSQL (5 caracteres)
PG_UNIQUE_VIOLATION = "23505"
PG_FOREIGN_KEY_VIOLATION = "23503"
PG_NOT_NULL_VIOLATION = "23502"
PG_CHECK_VIOLATION = "23514"
PG_SERIALIZATION_FAILURE = "40001"
PG_DEADLOCK_DETECTED = "40P01"

_LOC_TRANSPORT_PREFIXES: frozenset[str] = frozenset(
    {"body", "query", "path", "header", "cookie", "__root__"}
)

_INTERNAL_LOC_TOKEN_RE = re.compile(
    r"^(?:function-(?:after|before|wrap|plain)\[.*\]|tagged-union\[.*\]|constrained-.*)$"
)

_SCHEMA_CLASS_NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9_]*$")

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

PYDANTIC_SPANISH_FALLBACKS: dict[str, str] = {
    "string_too_short": "El texto es demasiado corto",
    "string_too_long": "El texto es demasiado largo",
    "greater_than": "El valor está por debajo del mínimo permitido",
    "greater_than_equal": "El valor está por debajo del mínimo permitido",
    "less_than": "El valor supera el máximo permitido",
    "less_than_equal": "El valor supera el máximo permitido",
    "multiple_of": "El valor no es un múltiplo válido",
}

CONSTRAINT_SPANISH_MESSAGES: dict[str, str] = {
    "uq_categories_name": "Ya existe una categoría con ese nombre",
    "categories_name_key": "Ya existe una categoría con ese nombre",
    "ix_categories_name": "Ya existe una categoría con ese nombre",
    "uq_dishes_name_category": "Ya existe un plato con ese nombre en la categoría",
    "dishes_category_id_fkey": "La categoría asociada no existe o no está disponible",
    "uq_users_email": "Ya existe un usuario registrado con ese correo electrónico",
    "users_email_key": "Ya existe un usuario registrado con ese correo electrónico",
    "uq_tables_number": "Ya existe una mesa con ese número",
}


def extract_field_name(
    loc: Sequence[str | int],
    error_type: str = "",
) -> str:
    """Extrae únicamente el nombre del campo hoja sin filtrar rutas internas ni esquemas.

    Ejemplo:
        ('body', 'usuario', 'direccion', 'codigo_postal') -> 'codigo_postal'
    """
    if not loc:
        return "cuerpo"

    filtered: list[str] = []
    for item in loc:
        if isinstance(item, int):
            continue
        token = str(item).strip()
        if not token or token in _LOC_TRANSPORT_PREFIXES:
            continue
        if token.isdigit() or _INTERNAL_LOC_TOKEN_RE.match(token):
            continue
        filtered.append(token)

    if not filtered:
        return "cuerpo"

    non_schema_tokens = [
        token for token in filtered if not _SCHEMA_CLASS_NAME_RE.match(token)
    ]
    if non_schema_tokens:
        return non_schema_tokens[-1]

    return filtered[-1].lower()


def _format_pydantic_message(error_type: str, ctx: Mapping[str, Any] | None) -> str:
    """Resuelve la plantilla en español para un tipo de error de Pydantic v2."""
    template = PYDANTIC_SPANISH_MESSAGES.get(error_type)
    if template is None:
        for prefix, msg in PYDANTIC_SPANISH_MESSAGES.items():
            if error_type.startswith(prefix):
                template = msg
                break

    if template is None:
        return "El valor proporcionado no es válido"

    if "{" not in template:
        return template

    safe_ctx: dict[str, Any] = {}
    if isinstance(ctx, Mapping):
        for key, value in ctx.items():
            if isinstance(value, (int, float, str)):
                safe_ctx[key] = value

    try:
        return template.format(**safe_ctx)
    except (KeyError, ValueError, IndexError):
        return PYDANTIC_SPANISH_FALLBACKS.get(
            error_type, "El valor proporcionado no es válido"
        )


def translate_validation_errors(errors: Sequence[Mapping[str, Any]]) -> str:
    """Traduce una secuencia de errores de Pydantic v2 a un único mensaje claro en español.

    Nunca incluye el campo `input` ni nombres de clases internas de esquemas.
    """
    if not errors:
        return "Datos de entrada inválidos"

    translated_items: list[str] = []
    for err in errors:
        error_type = str(err.get("type", ""))
        loc = err.get("loc", ())
        ctx = err.get("ctx") if isinstance(err.get("ctx"), Mapping) else None

        if error_type == "json_invalid":
            translated_items.append(PYDANTIC_SPANISH_MESSAGES["json_invalid"])
            continue

        field_name = extract_field_name(loc, error_type)
        reason = _format_pydantic_message(error_type, ctx)
        translated_items.append(f"Error en el campo '{field_name}': {reason}")

    return "; ".join(translated_items)


def extract_sqlstate(exc: BaseException) -> str | None:
    """Extrae el código SQLSTATE de 5 caracteres desde psycopg v3, psycopg2 o asyncpg."""
    orig = getattr(exc, "orig", None)
    cause = getattr(orig, "__cause__", None) if orig is not None else None
    diag = getattr(orig, "diag", None) if orig is not None else None
    cause_diag = getattr(cause, "diag", None) if cause is not None else None

    candidates = (
        getattr(orig, "sqlstate", None),
        getattr(orig, "pgcode", None),
        getattr(diag, "sqlstate", None),
        getattr(cause, "sqlstate", None),
        getattr(cause, "pgcode", None),
        getattr(cause_diag, "sqlstate", None),
        getattr(exc, "sqlstate", None),
        getattr(exc, "pgcode", None),
    )

    for candidate in candidates:
        if isinstance(candidate, str) and len(candidate) == 5:
            return candidate
    return None


def extract_constraint_name(exc: BaseException) -> str | None:
    """Extrae el nombre de la restricción violada tanto para psycopg v3 como asyncpg."""
    orig = getattr(exc, "orig", None)
    diag = getattr(orig, "diag", None) if orig is not None else None
    cause = getattr(orig, "__cause__", None) if orig is not None else None
    cause_diag = getattr(cause, "diag", None) if cause is not None else None
    exc_diag = getattr(exc, "diag", None)

    candidates = (
        getattr(diag, "constraint_name", None),
        getattr(orig, "constraint_name", None),
        getattr(cause, "constraint_name", None),
        getattr(cause_diag, "constraint_name", None),
        getattr(exc_diag, "constraint_name", None),
        getattr(exc, "constraint_name", None),
    )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def translate_sqlalchemy_error(exc: SQLAlchemyError) -> AppError:
    """Traduce excepciones de SQLAlchemy a excepciones puras de dominio en español."""
    sqlstate = extract_sqlstate(exc)
    constraint_name = extract_constraint_name(exc)
    internal_details: dict[str, Any] = {
        "db_exception_type": type(exc).__name__,
        "sqlstate": sqlstate,
        "constraint_name": constraint_name,
    }

    if sqlstate == PG_UNIQUE_VIOLATION:
        message = (
            CONSTRAINT_SPANISH_MESSAGES.get(constraint_name)
            if constraint_name
            else None
        ) or "El recurso ya existe o viola una restricción de unicidad"
        return ConflictError(
            message,
            error_code="UNIQUE_VIOLATION",
            internal_details=internal_details,
        )

    if sqlstate == PG_FOREIGN_KEY_VIOLATION:
        message = (
            CONSTRAINT_SPANISH_MESSAGES.get(constraint_name)
            if constraint_name
            else None
        ) or "Operación inválida por referencia a un recurso relacionado"
        return ConflictError(
            message,
            error_code="FOREIGN_KEY_VIOLATION",
            internal_details=internal_details,
        )

    if sqlstate == PG_NOT_NULL_VIOLATION:
        return DomainValidationError(
            "Falta un valor obligatorio requerido para completar la operación",
            error_code="NOT_NULL_VIOLATION",
            internal_details=internal_details,
        )

    if sqlstate == PG_CHECK_VIOLATION:
        return DomainValidationError(
            "Los datos proporcionados no cumplen las restricciones de validación",
            error_code="CHECK_VIOLATION",
            internal_details=internal_details,
        )

    if sqlstate in {PG_SERIALIZATION_FAILURE, PG_DEADLOCK_DETECTED}:
        return DatabaseRetryableError(
            "Conflicto temporal de concurrencia, por favor intente nuevamente",
            error_code="DATABASE_RETRYABLE_ERROR",
            internal_details=internal_details,
        )

    if isinstance(exc, IntegrityError):
        message = (
            CONSTRAINT_SPANISH_MESSAGES.get(constraint_name)
            if constraint_name
            else None
        ) or "Conflicto de integridad con el estado actual de los datos"
        return ConflictError(
            message,
            error_code="INTEGRITY_ERROR",
            internal_details=internal_details,
        )

    return InfrastructureError(
        "Error interno del servidor",
        error_code="DATABASE_INFRASTRUCTURE_ERROR",
        internal_details=internal_details,
    )


@contextmanager
def handle_db_exceptions(session: Session) -> Iterator[None]:
    """Intercepta errores en operaciones síncronas de BD garantizando session.rollback()."""
    try:
        yield
    except AppError:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        raise translate_sqlalchemy_error(exc) from exc
    except Exception as exc:
        session.rollback()
        raise InfrastructureError(
            "Error interno del servidor",
            internal_details={"unexpected_exception": type(exc).__name__},
        ) from exc


@asynccontextmanager
async def handle_async_db_exceptions(session: Any) -> AsyncIterator[None]:
    """Intercepta errores en operaciones asíncronas de BD garantizando await session.rollback()."""
    try:
        yield
    except AppError:
        await session.rollback()
        raise
    except SQLAlchemyError as exc:
        await session.rollback()
        raise translate_sqlalchemy_error(exc) from exc
    except Exception as exc:
        await session.rollback()
        raise InfrastructureError(
            "Error interno del servidor",
            internal_details={"unexpected_exception": type(exc).__name__},
        ) from exc


__all__ = [
    "CONSTRAINT_SPANISH_MESSAGES",
    "PG_CHECK_VIOLATION",
    "PG_DEADLOCK_DETECTED",
    "PG_FOREIGN_KEY_VIOLATION",
    "PG_NOT_NULL_VIOLATION",
    "PG_SERIALIZATION_FAILURE",
    "PG_UNIQUE_VIOLATION",
    "PYDANTIC_SPANISH_MESSAGES",
    "extract_constraint_name",
    "extract_field_name",
    "extract_sqlstate",
    "handle_async_db_exceptions",
    "handle_db_exceptions",
    "translate_sqlalchemy_error",
    "translate_validation_errors",
]
