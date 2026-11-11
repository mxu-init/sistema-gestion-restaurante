from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database_connection import get_db
from app.core.security import decode_access_token
from app.models.user_model import UserModel

# Habilita el boton Authorize de Swagger y lee el header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Jerarquia de roles: un rol superior hereda los permisos de los inferiores
ROLE_HIERARCHY = {
    "super_admin": 5,
    "admin": 4,
    "manager": 3,
    "staff": 2,
    "mesero": 1,
}


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    payload = decode_access_token(token)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No se pudo validar el token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(UserModel, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inexistente o inactivo",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*roles: str):
    def dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        user_level = ROLE_HIERARCHY.get(current_user.role, -1)
        requested_levels = [
            ROLE_HIERARCHY[role] for role in roles if role in ROLE_HIERARCHY
        ]
        allowed = current_user.role in roles or (
            bool(requested_levels) and user_level >= min(requested_levels)
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permisos para realizar esta operacion",
            )
        return current_user

    return dependency
