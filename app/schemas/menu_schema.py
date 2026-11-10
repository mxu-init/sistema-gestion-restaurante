from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MenuDishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal


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


class MenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    day: Optional[str] = None
    price: Decimal
    is_available: bool
    dishes: List[MenuDishRead]
