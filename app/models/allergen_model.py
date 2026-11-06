from sqlalchemy import Column, Integer, String
from app.core.database_connection import Base


class AllergenModel(Base):
    __tablename__ = "allergens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True, nullable=False)