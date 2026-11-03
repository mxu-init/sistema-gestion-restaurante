from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.dish_model import CategoryModel
from app.schemas.category_schema import CategoryUpdate

def get_categories(db: Session) -> List[CategoryModel]:
    return db.query(CategoryModel).all()

def get_category_by_id(db: Session, category_id: int) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.id == category_id).first()

def get_category_by_name(db: Session, name: str) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.name == name).first()

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
