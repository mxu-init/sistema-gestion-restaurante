from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth_dependencies import get_current_user, require_role
from app.core.database_connection import get_db
from app.core.security import create_access_token
from app.models.user_model import UserModel
from app.schemas.auth_schema import TokenResponse, UserResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm mapea el email del formulario en el campo username
    user = auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: UserModel = Depends(get_current_user)):
    return current_user


@router.get("/users", response_model=list[UserResponse])
def read_users(
    admin_user: UserModel = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return db.query(UserModel).all()
