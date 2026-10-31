from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0, description="El precio debe ser mayor a 0")
    is_available: bool = True
    category_id: int
    
class DishCreate(DishBase):
    pass

class DishUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    is_available: Optional[bool] = None
    category_id: Optional[int] = None
    
    
class DishResponse(DishBase):
    id: int
    image: Optional[str] = None
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True