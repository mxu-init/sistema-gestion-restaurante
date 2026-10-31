from pydantic import BaseModel
from typing import List
from app.schemas.dish_schema import DishResponse

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class CategoryWithDishesResponse(CategoryResponse):
    dishes: List[DishResponse] = []