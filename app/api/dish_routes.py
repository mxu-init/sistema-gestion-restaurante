from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database_connection import get_db
from app.schemas.dish_schema import DishCreate, DishUpdate, DishResponse
from app.services import dish_service, image_service, allergen_service

router = APIRouter(prefix="/dishes", tags=["Platos"])

@router.get("/", response_model=List[DishResponse])
def read_dishes(
    skip: int = Query(0, ge=0, description="Saltarse X registros:"),
    limit: int = Query(100, ge=1, le=200, description="Límite de registros por consulta:"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    is_available: Optional[bool] = Query(None, description="Filtrar por disponibilidad"),
    db: Session = Depends(get_db),
):
    return dish_service.get_dishes(
        db, skip=skip, limit=limit,
        category_id=category_id, is_available=is_available,
    )

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
    name: str = Form(..., min_length=1),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    category_id: int = Form(...),
    is_available: bool = Form(True),
    allergen_ids: List[int] = Form(default=[]),
    file: Optional[UploadFile] = File(None),
    image_url: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    name = name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El nombre no puede estar vacío"
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El nombre no puede exceder 100 caracteres"
        )

    if price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El precio debe ser mayor a 0"
        )

    if price > 99999999.99:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El precio debe ser menor o igual a 99999999.99"
        )

    if not dish_service.check_category_exists(db, category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: La categoría no existe"
        )

    if not allergen_service.check_allergens_exist(db, allergen_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: Uno o más alérgenos no existen"
        )

    existing_dish = dish_service.get_active_dish_by_name_and_category(db, name, category_id)
    if existing_dish:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato activo con ese nombre"
        )

    image = None
    if file:
        try:
            image = image_service.save_dish_image(file)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falla al registrar la imagen"
            )
    elif image_url:
        try:
            image = image_service.validate_image_url(image_url)
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )

    dish_data = DishCreate(
        name=name,
        description=description,
        price=price,
        category_id=category_id,
        is_available=is_available,
    )
    return dish_service.create_dish(db, dish_data, image, allergen_ids=allergen_ids)

@router.put("/{dish_id}", response_model=DishResponse)
def update_dish(dish_id: int, dish_data: DishUpdate, db: Session = Depends(get_db)):
    db_dish = dish_service.get_dish_by_id(db, dish_id=dish_id)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )

    update_data = dish_data.model_dump(exclude_unset=True)

    if "price" in update_data and update_data["price"] is not None:
        price = update_data["price"]
        if price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos del plato inválidos: El precio debe ser mayor a 0"
            )
        if price > 99999999.99:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos del plato inválidos: El precio debe ser menor o igual a 99999999.99"
            )

    if "category_id" in update_data and update_data["category_id"] is not None:
        if not dish_service.check_category_exists(db, update_data["category_id"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos del plato inválidos: La categoría no existe"
            )

    if "allergen_ids" in update_data and update_data["allergen_ids"] is not None:
        if not allergen_service.check_allergens_exist(db, update_data["allergen_ids"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Datos del plato inválidos: Uno o más alérgenos no existen"
            )

    if "image" in update_data and update_data["image"] is not None:
        try:
            update_data["image"] = image_service.validate_image_url(update_data["image"])
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )

    final_name = update_data.get("name", db_dish.name)
    final_category_id = update_data.get("category_id", db_dish.category_id)
    if final_name != db_dish.name or final_category_id != db_dish.category_id:
        existing_dish = dish_service.get_active_dish_by_name_and_category(db, final_name, final_category_id)
        if existing_dish and existing_dish.id != dish_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un plato activo con ese nombre"
            )

    db_dish = dish_service.update_dish(db=db, dish_id=dish_id, dish_data=dish_data)
    return db_dish

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    db_dish = dish_service.get_dish_by_id_including_deleted(db, dish_id)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    if db_dish.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Este plato ya fue eliminado"
        )
    dish_service.soft_delete_dish(db, dish_id)
    return None

@router.post("/{dish_id}/restore", response_model=DishResponse)
def restore_dish(dish_id: int, db: Session = Depends(get_db)):
    db_dish = dish_service.get_dish_by_id_including_deleted(db, dish_id)
    if not db_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    if db_dish.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El plato ya está activo"
        )
    existing_dish = dish_service.get_active_dish_by_name_and_category(db, db_dish.name, db_dish.category_id)
    if existing_dish and existing_dish.id != dish_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato activo con ese nombre"
        )
    restored_dish = dish_service.restore_dish(db, dish_id)
    if not restored_dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plato no encontrado"
        )
    return restored_dish
