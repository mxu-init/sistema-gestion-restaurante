from fastapi import FastAPI
from app.core.config import settings
from sqlalchemy import text
from app.core.database_connection import engine
from app.api import test_routes

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION
)

app.include_router(test_routes.router)

@app.get("/")
async def root():
    return "API Template"

@app.get("/health/db", tags=["Health"])
def check_database():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"message": "Conexión a la base de datos exitosa"}

# Para ejecutar: uvicorn app.main:app --reload
