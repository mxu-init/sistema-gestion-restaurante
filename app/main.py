from __future__ import annotations

from contextlib import asynccontextmanager
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Response, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api import (
    allergen_routes,
    category_routes,
    dish_routes,
    routes,
    test_routes,
)
from app.core.config import settings
from app.core.database_connection import engine
from app.core.handlers import register_exception_handlers
from app.core.logging_config import CorrelationIdMiddleware, configure_logging
from app.schemas.errors import COMMON_ERROR_RESPONSES, ErrorResponse
from app.services import reference_service

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    reference_service.ensure_reference_data_on_startup()
    yield


def configure_openapi(app_instance: FastAPI) -> None:
    """Sobrescribe el generador OpenAPI 3.1 para usar exclusivamente ErrorResponse en 422."""

    def custom_openapi() -> dict[str, Any]:
        if app_instance.openapi_schema:
            return app_instance.openapi_schema

        openapi_schema = get_openapi(
            title=app_instance.title,
            version=app_instance.version,
            description=app_instance.description,
            routes=app_instance.routes,
            openapi_version=app_instance.openapi_version,
        )

        components = openapi_schema.setdefault("components", {})
        schemas = components.setdefault("schemas", {})

        schemas["ErrorResponse"] = ErrorResponse.model_json_schema(
            ref_template="#/components/schemas/{model}"
        )
        schemas.pop("HTTPValidationError", None)
        schemas.pop("ValidationError", None)

        error_ref = {"$ref": "#/components/schemas/ErrorResponse"}

        for path_item in openapi_schema.get("paths", {}).values():
            if not isinstance(path_item, dict):
                continue
            for operation in path_item.values():
                if not isinstance(operation, dict):
                    continue
                responses = operation.get("responses")
                if not isinstance(responses, dict):
                    continue
                if "422" in responses:
                    responses["422"] = {
                        "description": "Error de validación de datos",
                        "content": {
                            "application/json": {
                                "schema": error_ref,
                            }
                        },
                    }

        app_instance.openapi_schema = openapi_schema
        return app_instance.openapi_schema

    app_instance.openapi = custom_openapi  # type: ignore[method-assign]


def create_app() -> FastAPI:
    """Factoría principal de la aplicación FastAPI."""
    configure_logging()

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        lifespan=lifespan,
        responses=COMMON_ERROR_RESPONSES,
    )

    application.add_middleware(CorrelationIdMiddleware)
    register_exception_handlers(application)

    os.makedirs(STATIC_DIR / "uploads", exist_ok=True)
    application.mount(
        "/static", StaticFiles(directory=str(STATIC_DIR)), name="static"
    )

    application.include_router(test_routes.router)
    application.include_router(dish_routes.router)
    application.include_router(category_routes.router)
    application.include_router(allergen_routes.router)
    application.include_router(routes.router)

    @application.get("/")
    async def root() -> str:
        return "API Template"

    @application.get("/favicon.ico", include_in_schema=False)
    @application.get("/docs/favicon.ico", include_in_schema=False)
    def favicon() -> Response:
        favicon_path = STATIC_DIR / "favicon.ico"
        if favicon_path.is_file():
            return FileResponse(favicon_path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @application.get("/health", tags=["Health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/health/db", tags=["Health"])
    def check_database() -> dict[str, str]:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"message": "Conexión a la base de datos exitosa"}

    configure_openapi(application)
    return application


app = create_app()
