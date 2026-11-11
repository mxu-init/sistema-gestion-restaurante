from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database_connection import get_db
from app.schemas.allergen_schema import AllergenResponse
from app.services import allergen_service

router = APIRouter(prefix="/allergens", tags=["Alérgenos"])

@router.get(
    "/",
    response_model=List[AllergenResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar alérgenos",
    description="Devuelve todos los alérgenos registrados.",
)
def get_allergens(db: Session = Depends(get_db)):
    return allergen_service.get_all_allergens(db)