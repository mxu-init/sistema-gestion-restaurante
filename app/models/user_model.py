from sqlalchemy import Boolean, Column, Integer, String
from app.core.database_connection import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String(50), nullable=False, default="mesero")
    is_active = Column(Boolean, nullable=False, default=True)
