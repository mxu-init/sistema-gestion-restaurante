from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.schemas.table_schema import TableCreate, TableResponse, TableUpdate
from app.services import table_service

router = APIRouter(prefix="/tables", tags=["Mesas"])


@router.get("/", response_model=List[TableResponse], status_code=status.HTTP_200_OK)
def read_tables(db: Session = Depends(get_db)):
    return table_service.get_tables(db=db)


@router.get("/{table_id}", response_model=TableResponse)
def read_table(table_id: int, db: Session = Depends(get_db)):
    db_table = table_service.get_table_by_id(db=db, table_id=table_id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )
    return db_table


@router.post("/", response_model=TableResponse, status_code=status.HTTP_201_CREATED)
def create_table(table_data: TableCreate, db: Session = Depends(get_db)):
    existing_table = table_service.get_table_by_number(db=db, number=table_data.number)
    if existing_table:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una mesa con ese número"
        )

    return table_service.create_table(db=db, table_data=table_data)


@router.put("/{table_id}", response_model=TableResponse)
def update_table(table_id: int, table_data: TableUpdate, db: Session = Depends(get_db)):
    db_table = table_service.get_table_by_id(db=db, table_id=table_id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )

    for field in ("number", "location", "capacity", "max_capacity", "is_active"):
        if field in table_data.model_fields_set and getattr(table_data, field) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Datos de la mesa inválidos: {field} no puede ser nulo"
            )

    if "number" in table_data.model_fields_set:
        same_number = table_service.get_table_by_number(db=db, number=table_data.number)
        if same_number and same_number.id != table_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una mesa con ese número"
            )

    capacity = table_data.capacity if "capacity" in table_data.model_fields_set else db_table.capacity
    max_capacity = table_data.max_capacity if "max_capacity" in table_data.model_fields_set else db_table.max_capacity
    if max_capacity < capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La capacidad máxima no puede ser menor que la capacidad"
        )

    return table_service.update_table(db=db, table_id=table_id, table_data=table_data)


@router.patch("/{table_id}/deactivate", response_model=TableResponse)
def deactivate_table(table_id: int, db: Session = Depends(get_db)):
    db_table = table_service.get_table_by_id(db=db, table_id=table_id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada"
        )

    return table_service.deactivate_table(db=db, table_id=table_id)
