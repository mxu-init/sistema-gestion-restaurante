from datetime import date, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import ReservationOrigin, ReservationStatus


class ReservationBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=1, max_length=20)
    num_people: int = Field(..., gt=0)
    reservation_date: date
    start_time: time
    table_id: int = Field(..., gt=0)
    origin: ReservationOrigin
    created_by: int = Field(..., gt=0)

    @field_validator("customer_name", "phone")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("El campo no puede estar vacío")
        return value


class ReservationCreate(ReservationBase):
    pass


class ReservationResponse(ReservationBase):
    id: int
    status: ReservationStatus

    model_config = ConfigDict(from_attributes=True)
