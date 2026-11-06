"""Configuración de logging estructurado JSON, sanitización y Pure ASGI Middleware de correlación."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import re
from typing import Any
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REDACTED_VALUE = "[REDACTED]"

correlation_id_ctx: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)

_SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "passwd",
        "pwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "jira_api_token",
        "authorization",
        "cookie",
        "set-cookie",
        "dsn",
        "database_url",
        "private_key",
        "client_secret",
        "credit_card",
        "cvv",
    }
)

_SENSITIVE_KEY_SUBSTRINGS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "dsn",
    "database_url",
)

_DSN_PATTERN = re.compile(
    r"\b(?:postgresql(?:\+[a-z0-9_]+)?|postgres|mysql(?:\+[a-z0-9_]+)?|sqlite|redis|amqp)://[^\s'\"]+",
    re.IGNORECASE,
)

_BEARER_PATTERN = re.compile(
    r"(Bearer\s+)[A-Za-z0-9\-._~+/]+=*",
    re.IGNORECASE,
)


def get_correlation_id() -> str | None:
    """Obtiene el identificador de correlación activo del contexto actual."""
    return correlation_id_ctx.get()


def _is_sensitive_key(key: str) -> bool:
    normalized = key.strip().lower().replace("-", "_")
    if normalized in _SENSITIVE_KEYS:
        return True
    return any(sub in normalized for sub in _SENSITIVE_KEY_SUBSTRINGS)


def _redact_string(value: str) -> str:
    redacted = _DSN_PATTERN.sub(REDACTED_VALUE, value)
    redacted = _BEARER_PATTERN.sub(rf"\1{REDACTED_VALUE}", redacted)
    return redacted


def redact_sensitive_data(data: Any) -> Any:
    """Enmascara recursivamente contraseñas, tokens, API keys y DSNs con `[REDACTED]`."""
    if isinstance(data, Mapping):
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            key_str = str(key)
            if _is_sensitive_key(key_str):
                sanitized[key_str] = REDACTED_VALUE
            else:
                sanitized[key_str] = redact_sensitive_data(value)
        return sanitized

    if isinstance(data, list):
        return [redact_sensitive_data(item) for item in data]

    if isinstance(data, tuple):
        return tuple(redact_sensitive_data(item) for item in data)

    if isinstance(data, str):
        return _redact_string(data)

    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formateador JSON estructurado con inyección automática de correlation_id y sanitización."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _redact_string(record.getMessage()),
            "correlation_id": get_correlation_id(),
        }

        extra_context = getattr(record, "context", None)
        if extra_context is not None:
            payload["context"] = redact_sensitive_data(extra_context)

        error_code = getattr(record, "error_code", None)
        if error_code is not None:
            payload["error_code"] = error_code

        if record.exc_info:
            exc_type = record.exc_info[0]
            payload["exception_type"] = (
                exc_type.__name__ if exc_type is not None else "Exception"
            )

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura y devuelve el logger estructurado de la aplicación."""
    logger = logging.getLogger("sgr")
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(StructuredJsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


class CorrelationIdMiddleware:
    """Pure ASGI Middleware para propagar `X-Request-ID` y sincronizar con `ContextVar`.

    No utiliza BaseHTTPMiddleware ni intercepta el flujo de excepciones de dominio.
    """

    def __init__(
        self,
        app: ASGIApp,
        header_name: str = "X-Request-ID",
    ) -> None:
        self.app = app
        self.header_name = header_name
        self._header_name_bytes = header_name.lower().encode("latin-1")

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id: str | None = None
        for raw_name, raw_value in scope.get("headers", []):
            if raw_name.lower() == self._header_name_bytes:
                decoded = raw_value.decode("latin-1").strip()
                if decoded:
                    request_id = decoded
                break

        if not request_id:
            request_id = str(uuid.uuid4())

        state: MutableMapping[str, Any] = scope.setdefault("state", {})
        state["correlation_id"] = request_id

        token = correlation_id_ctx.set(request_id)

        async def send_with_correlation_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                raw_headers = list(message.get("headers", []))
                has_header = any(
                    k.lower() == self._header_name_bytes for k, _ in raw_headers
                )
                if not has_header:
                    raw_headers.append(
                        (
                            self.header_name.encode("latin-1"),
                            request_id.encode("latin-1"),
                        )
                    )
                message["headers"] = raw_headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_correlation_id)
        finally:
            correlation_id_ctx.reset(token)


__all__ = [
    "CorrelationIdMiddleware",
    "REDACTED_VALUE",
    "StructuredJsonFormatter",
    "configure_logging",
    "correlation_id_ctx",
    "get_correlation_id",
    "redact_sensitive_data",
]
