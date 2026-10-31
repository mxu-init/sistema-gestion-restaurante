from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database_connection import get_db
from app.schemas.dish_schema import DishCreate, DishUpdate, DishResponse
from app.services import dish_service, image_service

router = APIRouter(prefix="/dishes", tags=["Platos"])

@router.get("/", response_model=List[DishResponse])
def read_dishes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return dish_service.get_dishes(db, skip=skip, limit=limit)

@router.get("/{dish_id}", response_model=DishResponse)
def read_dish_by_id(dish_id: int, db: Session = Depends(get_db)):
    db_dish = dish_service.get_dish_by_id(db, dish_id=dish_id)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    return db_dish

@router.post("/", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def create_dish(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    category_id: int = Form(...),
    is_available: bool = Form(True),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El precio debe ser mayor a 0"
        )

    if not dish_service.check_category_exists(db, category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: La categoría no existe"
        )

    existing_dish = dish_service.get_active_dish_by_name_and_category(db, name, category_id)
    if existing_dish:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato activo con ese nombre"
        )

    image_url = None
    if file:
        try:
            image_url = image_service.save_dish_image(file)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falla al registrar la imagen"
            )

    dish_data = DishCreate(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        is_available=is_available
    )
    return dish_service.create_dish(db, dish_data, image_url)

@router.put("/{dish_id}", response_model=DishResponse)
def update_dish(dish_id: int, dish_data: DishUpdate, db: Session = Depends(get_db)):
    db_dish = dish_service.update_dish(db=db, dish_id=dish_id, dish_data=dish_data)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    return db_dish

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    db_dish = dish_service.soft_delete_dish(db, dish_id)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    return None