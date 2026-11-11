from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database_connection import get_db
from app.schemas.category_schema import CategoryCreate, CategoryResponse, CategoryUpdate, CategoryWithDishesResponse
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["Categorías"])

@router.get(
    "/",
    response_model=List[CategoryResponse],
    summary="Listar categorías",
    description="Devuelve todas las categorías registradas.",
)
def read_categories(db: Session = Depends(get_db)):
    return category_service.get_categories(db=db)

@router.get(
    "/{category_id}/dishes",
    response_model=CategoryWithDishesResponse,
    summary="Listar categoría con sus platos",
    description="Devuelve una categoría por su id junto con los platos asociados.",
)
def read_category_with_dishes(category_id: int, db: Session = Depends(get_db)):
    category = category_service.get_category_by_id(db=db, category_id=category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return category

@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría",
    description="Registra una categoría nueva. El nombre debe ser único.",
)
def create_category(category_data: CategoryCreate, db: Session = Depends(get_db)):
    category_data.name = category_data.name.strip()
    if not category_data.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos de la categoría inválidos: El nombre no puede estar vacío"
        )

    existing_category = category_service.get_category_by_name(db=db, name=category_data.name)
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una categoría con ese nombre"
        )

    return category_service.create_category(db=db, category_data=category_data)

@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Actualizar categoría",
    description="Modifica el nombre de una categoría existente. El nuevo nombre debe ser único.",
)
def update_category(category_id: int, category_data: CategoryUpdate, db: Session = Depends(get_db)):
    db_category = category_service.get_category_by_id(db=db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    if "name" in category_data.model_fields_set:
        if category_data.name is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos de la categoría inválidos: El nombre no puede ser nulo"
            )
        category_data.name = category_data.name.strip()
        if not category_data.name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos de la categoría inválidos: El nombre no puede estar vacío"
            )
        same_name = category_service.get_category_by_name(db=db, name=category_data.name)
        if same_name and same_name.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una categoría con ese nombre"
            )

    return category_service.update_category(db=db, category_id=category_id, category_data=category_data)

@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar categoría",
    description="Elimina una categoría. No se puede eliminar si tiene platos asociados.",
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_category = category_service.get_category_by_id(db=db, category_id=category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )

    if category_service.category_has_dishes(db=db, category_id=category_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar una categoría que tiene platos asociados"
        )

    category_service.delete_category(db=db, category_id=category_id)
    return None