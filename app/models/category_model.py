from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database_connection import Base


class CategoryModel(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    active_dishes = relationship(
        "DishModel",
        primaryjoin="and_(CategoryModel.id == DishModel.category_id, DishModel.deleted_at.is_(None))",
        back_populates="category",
        viewonly=True,
    )
