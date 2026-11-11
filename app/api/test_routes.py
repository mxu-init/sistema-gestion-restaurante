from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database_connection import get_db
from app.schemas.test_schema import TestCreate
from app.controllers.test_controller import create_test


router = APIRouter(prefix="/test", tags=["Pruebas"])

@router.post(
    "/",
    status_code=201,
    summary="Crear registro de prueba",
    description="Endpoint de demostración que guarda un registro de prueba en la tabla test.",
)
def create_new_test(test:TestCreate, db:Session = Depends(get_db)):
    return create_test(db=db, test=test)
