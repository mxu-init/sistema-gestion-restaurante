from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database_connection import get_db
from app.schemas.category_schema import CategoryResponse, CategoryWithDishesResponse
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categorías"])

@router.get("/", response_model=List[CategoryResponse])
def read_categories(db: Session = Depends(get_db)):
    return category_service.get_categories(db=db)

@router.get("/{category_id}/dishes", response_model=CategoryWithDishesResponse)
def read_category_with_dishes(category_id: int, db: Session = Depends(get_db)):
    category = category_service.get_category_by_id(db=db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return category