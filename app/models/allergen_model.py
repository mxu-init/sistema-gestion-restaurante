from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database_connection import Base
from app.models.dish_allergen_model import dish_allergens


class AllergenModel(Base):
    __tablename__ = "allergens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)

    dishes = relationship(
        "DishModel",
        secondary=dish_allergens,
        back_populates="allergens",
    )
