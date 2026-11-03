from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.models.dish_model import CategoryModel
from app.schemas.dish_schema import DishCreate, DishResponse
from app.schemas.external_schema import ExternalImportRequest, ExternalSearchItem, ExternalSource
from app.services import dish_service, external_service

router = APIRouter(prefix="/external", tags=["External APIs"])

CATEGORY_SUGGESTIONS = {
    "cocktaildb": "bebidas",
    "mealdb": "comida",
}


def _suggest_category_id(db: Session, source: ExternalSource, external_category: str | None) -> int | None:
    target_name = CATEGORY_SUGGESTIONS[source]
    if source == "mealdb" and external_category and external_category.strip().lower() == "dessert":
        target_name = "postres"
    categories = db.query(CategoryModel).all()
    for category in categories:
        if category.name and category.name.strip().lower() == target_name:
            return category.id
    return None


@router.get("/search", response_model=List[ExternalSearchItem])
def search_external(
    source: ExternalSource = Query(..., description="mealdb para alimentos/postres, cocktaildb para bebidas"),
    q: str = Query(..., min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    try:
        if source == "mealdb":
            results = external_service.search_meals(q)
        else:
            results = external_service.search_drinks(q)
    except external_service.ExternalApiError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio externo no está disponible en este momento, intente más tarde",
        ) from error

    return [
        ExternalSearchItem(
            **result,
            suggested_category_id=_suggest_category_id(db, source, result.get("category")),
        )
        for result in results
    ]


@router.post("/import", response_model=DishResponse, status_code=status.HTTP_201_CREATED)
def import_external(payload: ExternalImportRequest, db: Session = Depends(get_db)):
    if not dish_service.check_category_exists(db, payload.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: La categoría no existe",
        )

    try:
        product = external_service.lookup_product(payload.source, payload.source_id)
    except external_service.ExternalApiError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="El servicio externo no está disponible en este momento, intente más tarde",
        ) from error
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado en el servicio externo",
        )

    name = (payload.name or product["name"]).strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El nombre no puede estar vacío",
        )
    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Datos del plato inválidos: El nombre no puede exceder 100 caracteres",
        )

    if dish_service.get_active_dish_by_name_and_category(db, name, payload.category_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un plato activo con ese nombre",
        )

    description = payload.description if payload.description is not None else product.get("description")

    image_url = None
    if product.get("image_url"):
        image_url = product["image_url"].strip() or None

    dish_data = DishCreate(
        name=name,
        description=description,
        price=payload.price,
        category_id=payload.category_id,
        is_available=payload.is_available,
    )
    try:
        return dish_service.create_dish(
            db,
            dish_data,
            image_url=image_url,
        )
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este producto ya fue importado anteriormente",
        ) from error
