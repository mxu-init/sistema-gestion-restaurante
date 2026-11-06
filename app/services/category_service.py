from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import CategoryModel, DishModel
from app.schemas.category_schema import CategoryCreate, CategoryUpdate

def get_categories(db: Session) -> List[CategoryModel]:
    return db.query(CategoryModel).all()

def get_category_by_id(db: Session, category_id: int) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.name == name).first()

def category_has_dishes(db: Session, category_id: int) -> bool:
    return db.query(DishModel.id).filter(DishModel.category_id == category_id).first() is not None

def create_category(db: Session, category_data: CategoryCreate) -> CategoryModel:
    new_category = CategoryModel(**category_data.model_dump())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

def update_category(db: Session, category_id: int, category_data: CategoryUpdate) -> Optional[CategoryModel]:
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None

    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db.commit()
    db.refresh(db_category)
    return db_category

def delete_category(db: Session, category_id: int) -> Optional[CategoryModel]:
    db_category = get_category_by_id(db, category_id)
    if not db_category:
        return None

    db.delete(db_category)
    db.commit()
    return db_category
