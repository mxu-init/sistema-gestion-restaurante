from sqlalchemy.orm import Session
from app.models.test_model import TestModel
from app.schemas.test_schema import TestCreate

def create_test(db: Session, test: TestCreate):
    db_test = TestModel(test_name=test.test_name, test_type=test.test_type)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test