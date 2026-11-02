from typing import Literal, Optional

from pydantic import BaseModel, Field

ExternalSource = Literal["mealdb", "cocktaildb"]


class ExternalSearchItem(BaseModel):
    source: ExternalSource
    source_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    suggested_category_id: Optional[int] = None


class ExternalImportRequest(BaseModel):
    source: ExternalSource
    source_id: str = Field(..., min_length=1, max_length=50)
    category_id: int
    price: float = Field(..., gt=0, le=99999999.99)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_available: bool = True
