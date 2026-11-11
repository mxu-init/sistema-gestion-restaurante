from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user_model import UserModel


def authenticate_user(db: Session, email: str, password: str) -> UserModel:
    user = db.query(UserModel).filter(UserModel.email == email).first()

    if (
        not user
        or not verify_password(password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
