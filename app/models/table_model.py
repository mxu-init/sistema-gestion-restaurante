from sqlalchemy import Boolean, CheckConstraint, Column, Integer, String
from app.core.database_connection import Base


class TableModel(Base):
    __tablename__ = "tables"
    __table_args__ = (
        CheckConstraint("number > 0", name="ck_tables_number_positive"),
        CheckConstraint("location IN ('indoor', 'outdoor', 'terrace')", name="ck_tables_location"),
        CheckConstraint("capacity > 0", name="ck_tables_capacity"),
        CheckConstraint("max_capacity >= capacity", name="ck_tables_max_capacity"),
    )

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True, nullable=False)
    location = Column(String(20), nullable=False)
    capacity = Column(Integer, nullable=False)
    max_capacity = Column(Integer, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
