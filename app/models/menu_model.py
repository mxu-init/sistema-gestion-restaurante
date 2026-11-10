from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.core.database_connection import Base

menu_dishes = Table(
    "menu_dishes",
    Base.metadata,
    Column("menu_id", Integer, ForeignKey("menus.id"), primary_key=True),
    Column("dish_id", Integer, ForeignKey("dishes.id"), primary_key=True),
)


class MenuModel(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    price = Column(Numeric(8, 2), nullable=False)
    is_available = Column(Boolean, nullable=False, default=True, server_default="true")
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    dishes = relationship("DishModel", secondary=menu_dishes)

