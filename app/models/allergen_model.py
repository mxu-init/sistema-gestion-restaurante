from sqlalchemy import Column, Integer, String, ForeignKey, Table
from app.core.database_connection import Base

dish_allergens = Table(
    "dish_allergens",
    Base.metadata,
    Column("dish_id", Integer, ForeignKey("dishes.id"), primary_key=True),
    Column("allergen_id", Integer, ForeignKey("allergens.id"), primary_key=True),
)

class AllergenModel(Base):
    __tablename__ = "allergens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)
