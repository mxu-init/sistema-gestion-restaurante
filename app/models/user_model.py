from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database_connection import Base

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # longitud 50 heredada de la migracion aplicada en la rama jwt (no destructivo)
    role = Column(String(50), nullable=False, default="staff")
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
