import logging
from typing import List, Type

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.core.database_connection import engine, session_local
from app.core.reference_data import BASE_CATEGORIES, EU_ALLERGENS
from app.models import AllergenModel, CategoryModel

logger = logging.getLogger(__name__)


def _insert_missing(db: Session, model: Type, names: List[str]) -> None:
    existing = {name for (name,) in db.query(model.name).all()}
    for name in names:
        if name not in existing:
            db.add(model(name=name))
    db.commit()


def ensure_reference_data(db: Session) -> None:
    """Insert any missing base category or allergen. Idempotent."""
    _insert_missing(db, CategoryModel, BASE_CATEGORIES)
    _insert_missing(db, AllergenModel, EU_ALLERGENS)


def ensure_reference_data_on_startup() -> None:
    """Restore fixed reference data when the API boots, if the schema is migrated."""
    inspector = inspect(engine)
    missing_tables = [
        table for table in ("categories", "allergens")
        if not inspector.has_table(table)
    ]
    if missing_tables:
        logger.warning(
            "Skipping reference data check, table(s) not migrated yet: %s",
            ", ".join(missing_tables),
        )
        return

    db = session_local()
    try:
        ensure_reference_data(db)
    finally:
        db.close()
