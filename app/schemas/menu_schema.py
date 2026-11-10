from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MenuDishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal
    is_available: bool = True


class MenuCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(default="estándar", min_length=1, max_length=50)
    day: Optional[str] = Field(None, max_length=50)
    price: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    dish_ids: List[int] = Field(min_length=1)

    @field_validator("name", "type", mode="after")
    @classmethod
    def validate_non_empty_strings(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("El valor no puede estar vacío")
        return trimmed

    @field_validator("day", mode="after")
    @classmethod
    def validate_day(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            trimmed = value.strip()
            return trimmed if trimmed else None
        return value


class MenuUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    day: Optional[str] = Field(None, max_length=50)
    price: Optional[Decimal] = Field(None, ge=0, max_digits=8, decimal_places=2)
    dish_ids: Optional[List[int]] = Field(None, min_length=1)
    is_available: Optional[bool] = None

    @field_validator("name", "type", mode="after")
    @classmethod
    def validate_optional_non_empty_strings(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            trimmed = value.strip()
            if not trimmed:
                raise ValueError("El valor no puede estar vacío")
            return trimmed
        return value

    @field_validator("day", mode="after")
    @classmethod
    def validate_optional_day(cls, value: Optional[str]) -> Optional[str]:
        if value is not None:
            trimmed = value.strip()
            return trimmed if trimmed else None
        return value


class MenuAvailabilityUpdate(BaseModel):
    is_available: bool = Field(..., description="Estado de disponibilidad manual del menú")


class MenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    day: Optional[str] = None
    price: Decimal
    is_available: bool
    dishes: List[MenuDishRead]

    @model_validator(mode="wrap")
    @classmethod
    def wrap_validation(cls, data: Any, handler):
        instance = handler(data)
        if hasattr(data, "is_effectively_available"):
            instance.is_available = bool(data.is_effectively_available)
        elif hasattr(data, "dishes") and hasattr(data, "is_available"):
            dishes = getattr(data, "dishes", [])
            manual_avail = getattr(data, "is_available", True)
            instance.is_available = (
                bool(manual_avail)
                and len(dishes) > 0
                and all(
                    getattr(d, "is_available", False)
                    and getattr(d, "deleted_at", None) is None
                    for d in dishes
                )
            )
        return instance
