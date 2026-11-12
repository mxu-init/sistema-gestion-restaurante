import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api import (
    allergen_routes,
    auth_routes,
    category_routes,
    dish_routes,
    menu_routes,
    test_routes,
)
from app.services import reference_service, user_service
from app.core.exceptions import register_exception_handlers
from app.schemas.errors import COMMON_ERROR_RESPONSES

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    reference_service.ensure_reference_data_on_startup()
    user_service.ensure_super_admin_on_startup()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    responses=COMMON_ERROR_RESPONSES,
)

register_exception_handlers(app)

os.makedirs(STATIC_DIR / "uploads", exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(dish_routes.router)
app.include_router(category_routes.router)
app.include_router(allergen_routes.router)
app.include_router(auth_routes.router)
app.include_router(menu_routes.router)

@app.get("/", summary="Inicio de la API", description="Mensaje de bienvenida de la API.")
async def root():
    return "API Template"

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/docs/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    return FileResponse(favicon_path)


