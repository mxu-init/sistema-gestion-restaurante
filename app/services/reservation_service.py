from datetime import date, time
from typing import Optional

from sqlalchemy.orm import Session

from app.core.enums import ReservationStatus
from app.models.reservation_model import ReservationModel
from app.models.table_model import TableModel
from app.schemas.reservation_schema import ReservationCreate


ACTIVE_RESERVATION_STATUSES = ("pending", "confirmed", "seated")


def get_table_by_id(db: Session, table_id: int) -> Optional[TableModel]:
    return db.query(TableModel).filter(TableModel.id == table_id).first()


def get_active_reservation_by_table(
    db: Session,
    table_id: int,
    reservation_date: date,
    start_time: time,
) -> Optional[ReservationModel]:
    return db.query(ReservationModel).filter(
        ReservationModel.table_id == table_id,
        ReservationModel.reservation_date == reservation_date,
        ReservationModel.start_time == start_time,
        ReservationModel.status.in_(ACTIVE_RESERVATION_STATUSES),
    ).first()


def get_active_reservation_by_phone(
    db: Session,
    phone: str,
    reservation_date: date,
    start_time: time,
) -> Optional[ReservationModel]:
    return db.query(ReservationModel).filter(
        ReservationModel.phone == phone,
        ReservationModel.reservation_date == reservation_date,
        ReservationModel.start_time == start_time,
        ReservationModel.status.in_(ACTIVE_RESERVATION_STATUSES),
    ).first()


def create_reservation(
    db: Session,
    reservation_data: ReservationCreate,
) -> ReservationModel:
    new_reservation = ReservationModel(
        **reservation_data.model_dump(),
        status=ReservationStatus.CONFIRMED.value,
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return new_reservation
