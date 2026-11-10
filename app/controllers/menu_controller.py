from typing import List

from sqlalchemy.orm import Session

from app.models.menu_model import MenuModel
from app.schemas.menu_schema import MenuCreate
from app.services import menu_service


def create_menu(db: Session, menu_data: MenuCreate) -> MenuModel:
    return menu_service.create_menu(db, menu_data)


def get_menus(db: Session) -> List[MenuModel]:
    return menu_service.fetch_menus(db)


def get_menu_by_id(db: Session, menu_id: int) -> MenuModel:
    return menu_service.fetch_menu_by_id(db, menu_id)

