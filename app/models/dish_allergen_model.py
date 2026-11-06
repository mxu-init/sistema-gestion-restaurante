from sqlalchemy import Column, Integer, ForeignKey, Table
from app.core.database_connection import Base

dish_allergens = Table(
    "dish_allergens",
    Base.metadata,
    Column("dish_id", Integer, ForeignKey("dishes.id"), primary_key=True),
    Column("allergen_id", Integer, ForeignKey("allergens.id"), primary_key=True),
)