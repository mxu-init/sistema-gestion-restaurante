from typing import List
from sqlalchemy.orm import Session
from app.models import AllergenModel

def get_all_allergens(db: Session) -> List[AllergenModel]:
    return db.query(AllergenModel).order_by(AllergenModel.id.asc()).all()
