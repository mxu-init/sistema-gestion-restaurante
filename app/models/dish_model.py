from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database_connection import Base

class CategoryModel(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    dishes = relationship("DishModel", back_populates="category")
    
class DishModel(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    price = Column(Numeric(8, 2), nullable=False)
    is_available = Column(Boolean, default=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    image = Column(String, nullable=True)

    category = relationship("CategoryModel", back_populates="dishes")