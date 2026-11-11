import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.core.config import settings
from app.core.database_connection import engine
from app.api import test_routes, dish_routes, category_routes, allergen_routes, menu_routes
from app.services import reference_service
from app.core.exceptions import register_exception_handlers
from app.schemas.errors import COMMON_ERROR_RESPONSES

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    reference_service.ensure_reference_data_on_startup()
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

app.include_router(test_routes.router)
app.include_router(dish_routes.router)
app.include_router(category_routes.router)
app.include_router(allergen_routes.router)
app.include_router(menu_routes.router)

@app.get("/")
async def root():
    return "API Template"

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/docs/favicon.ico", include_in_schema=False)
def favicon():
    favicon_path = STATIC_DIR / "favicon.ico"
    return FileResponse(favicon_path)

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/health/db", tags=["Health"])
def check_database():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"message": "Conexión a la base de datos exitosa"}
