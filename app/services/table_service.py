from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.table_model import TableModel
from app.schemas.table_schema import TableCreate, TableUpdate


def get_tables(db: Session) -> List[TableModel]:
    return db.query(TableModel).order_by(TableModel.number.asc()).all()


def get_table_by_id(db: Session, table_id: int) -> Optional[TableModel]:
    return db.query(TableModel).filter(TableModel.id == table_id).first()


def get_table_by_number(db: Session, number: int) -> Optional[TableModel]:
    return db.query(TableModel).filter(TableModel.number == number).first()


def create_table(db: Session, table_data: TableCreate) -> TableModel:
    new_table = TableModel(**table_data.model_dump())
    db.add(new_table)
    db.commit()
    db.refresh(new_table)
    return new_table


def update_table(db: Session, table_id: int, table_data: TableUpdate) -> Optional[TableModel]:
    db_table = get_table_by_id(db, table_id)
    if not db_table:
        return None

    update_data = table_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_table, key, value)

    db.commit()
    db.refresh(db_table)
    return db_table


def deactivate_table(db: Session, table_id: int) -> Optional[TableModel]:
    db_table = get_table_by_id(db, table_id)
    if not db_table:
        return None

    db_table.is_active = False
    db.commit()
    db.refresh(db_table)
    return db_table
