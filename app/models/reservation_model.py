from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, Time

from app.core.database_connection import Base
from app.core.enums import ReservationStatus


class ReservationModel(Base):
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("num_people > 0", name="ck_reservations_num_people"),
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'seated', 'cancelled', 'no_show')",
            name="ck_reservations_status",
        ),
        CheckConstraint(
            "origin IN ('phone', 'in_person')",
            name="ck_reservations_origin",
        ),
        CheckConstraint("created_by > 0", name="ck_reservations_created_by"),
        Index(
            "ix_reservations_table_slot",
            "table_id",
            "reservation_date",
            "start_time",
        ),
        Index(
            "ix_reservations_phone_slot",
            "phone",
            "reservation_date",
            "start_time",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    num_people = Column(Integer, nullable=False)
    reservation_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    table_id = Column(Integer, ForeignKey("tables.id"), nullable=False)
    status = Column(
        String(20),
        nullable=False,
        default=ReservationStatus.CONFIRMED.value,
        server_default=ReservationStatus.CONFIRMED.value,
    )
    origin = Column(String(20), nullable=False)
    created_by = Column(Integer, nullable=False)
