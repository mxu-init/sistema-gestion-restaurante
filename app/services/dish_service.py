from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.dish_model import DishModel, CategoryModel
from app.schemas.dish_schema import DishCreate, DishUpdate

def check_category_exists(db: Session, category_id: int) -> bool:
    return db.query(CategoryModel).filter(CategoryModel.id == category_id).first() is not None

def get_active_dish_by_name_and_category(db: Session, name: str, category_id: int) -> Optional[DishModel]:
    return db.query(DishModel).filter(
        func.lower(DishModel.name) == name.lower(),
        DishModel.category_id == category_id,
        DishModel.deleted_at.is_(None)
    ).first()

def get_dishes(db: Session, skip: int = 0, limit: int = 100):
    return (
        db.query(DishModel)
        .filter(DishModel.deleted_at.is_(None))
        .order_by(DishModel.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def get_dish_by_id(db: Session, dish_id: int) -> Optional[DishModel]:
    return db.query(DishModel).filter(DishModel.id == dish_id, DishModel.deleted_at.is_(None)).first()

def create_dish(db: Session, dish_data: DishCreate, image_url: Optional[str] = None) -> DishModel:
    new_dish = DishModel(
        **dish_data.model_dump(),
        image=image_url
    )
    db.add(new_dish)
    db.commit()
    db.refresh(new_dish)
    return new_dish

def update_dish(db: Session, dish_id: int, dish_data: DishUpdate) -> Optional[DishModel]:
    db_dish = get_dish_by_id(db, dish_id)
    if not db_dish:
        return None
    
    update_data = dish_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_dish, key, value)
    
    db.commit()
    db.refresh(db_dish)
    return db_dish

def soft_delete_dish(db: Session, dish_id: int) -> Optional[DishModel]:
    db_dish = get_dish_by_id(db, dish_id)
    if not db_dish:
        return None
    db_dish.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return db_dish