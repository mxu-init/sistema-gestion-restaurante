from typing import List
from sqlalchemy.orm import Session
from app.models import AllergenModel

def get_all_allergens(db: Session) -> List[AllergenModel]:
    return db.query(AllergenModel).order_by(AllergenModel.id.asc()).all()

def get_allergens_by_ids(db: Session, allergen_ids: List[int]) -> List[AllergenModel]:
    unique_ids = list(dict.fromkeys(allergen_ids))
    if not unique_ids:
        return []
    allergens = db.query(AllergenModel).filter(AllergenModel.id.in_(unique_ids)).all()
    order = {allergen_id: index for index, allergen_id in enumerate(unique_ids)}
    return sorted(allergens, key=lambda allergen: order[allergen.id])

def check_allergens_exist(db: Session, allergen_ids: List[int]) -> bool:
    unique_ids = set(allergen_ids)
    if not unique_ids:
        return True
    found = db.query(AllergenModel.id).filter(AllergenModel.id.in_(unique_ids)).all()
    return len(found) == len(unique_ids)
