from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class TableBase(BaseModel):
    number: int = Field(..., gt=0)
    location: Literal["indoor", "outdoor", "terrace"]
    capacity: int = Field(..., gt=0)
    max_capacity: int = Field(..., gt=0)
    is_active: bool = True

    @model_validator(mode="after")
    def validate_capacity(self):
        if self.max_capacity < self.capacity:
            raise ValueError("max_capacity debe ser mayor o igual que capacity")
        return self


class TableCreate(TableBase):
    pass


class TableUpdate(BaseModel):
    number: Optional[int] = Field(None, gt=0)
    location: Optional[Literal["indoor", "outdoor", "terrace"]] = None
    capacity: Optional[int] = Field(None, gt=0)
    max_capacity: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class TableResponse(TableBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
