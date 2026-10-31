from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.dish_model import CategoryModel

def get_categories(db: Session) -> List[CategoryModel]:
    return db.query(CategoryModel).all()

def get_category_by_id(db: Session, category_id: int) -> Optional[CategoryModel]:
    return db.query(CategoryModel).filter(CategoryModel.id == category_id).first()