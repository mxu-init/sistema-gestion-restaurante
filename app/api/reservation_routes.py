from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.schemas.reservation_schema import ReservationCreate, ReservationResponse
from app.services import reservation_service

router = APIRouter(prefix="/reservations", tags=["Reservas"])


@router.post("/", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db),
):
    if (
        reservation_data.start_time.minute != 0
        or reservation_data.start_time.second != 0
        or reservation_data.start_time.microsecond != 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La hora de inicio debe ser en punto",
        )

    start_at = datetime.combine(
        reservation_data.reservation_date,
        reservation_data.start_time,
    )
    if start_at <= datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha y hora de inicio deben ser futuras",
        )

    db_table = reservation_service.get_table_by_id(db, reservation_data.table_id)
    if not db_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mesa no encontrada",
        )

    if not db_table.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La mesa no está activa",
        )

    if reservation_data.num_people > db_table.max_capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La mesa no admite el número de personas indicado",
        )

    table_reservation = reservation_service.get_active_reservation_by_table(
        db,
        reservation_data.table_id,
        reservation_data.reservation_date,
        reservation_data.start_time,
    )
    if table_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La mesa ya tiene una reserva activa en esa franja horaria",
        )

    phone_reservation = reservation_service.get_active_reservation_by_phone(
        db,
        reservation_data.phone,
        reservation_data.reservation_date,
        reservation_data.start_time,
    )
    if phone_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El teléfono ya tiene una reserva activa en esa franja horaria",
        )

    return reservation_service.create_reservation(db, reservation_data)
