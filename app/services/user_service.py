from app.core.config import settings
from app.core.database_connection import session_local
from app.core.security import get_password_hash
from app.models import UserModel


def ensure_super_admin_on_startup() -> None:
    # Sin email configurado no hay bootstrap que hacer
    if not settings.SUPER_ADMIN_EMAIL:
        return

    db = session_local()
    try:
        existing_user = db.query(UserModel).filter(
            UserModel.email == settings.SUPER_ADMIN_EMAIL
        ).first()
        if existing_user:
            return

        super_admin = UserModel(
            name=settings.SUPER_ADMIN_NAME,
            email=settings.SUPER_ADMIN_EMAIL,
            password_hash=get_password_hash(settings.SUPER_ADMIN_PASSWORD),
            role="super_admin",
        )
        db.add(super_admin)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()