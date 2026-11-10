from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MenuDishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: Decimal


class MenuCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=50)
    price: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    dish_ids: list[int] = Field(min_length=1)


class MenuRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: str
    price: Decimal
    is_available: bool
    dishes: list[MenuDishRead]

