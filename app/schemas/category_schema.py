from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.dish_schema import DishResponse

class CategoryBase(BaseModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True

class CategoryWithDishesResponse(CategoryResponse):
    dishes: List[DishResponse] = []
