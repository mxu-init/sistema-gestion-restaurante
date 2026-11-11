from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.menu_model import MenuModel
from app.schemas.menu_schema import MenuCreate, MenuUpdate
from app.services import menu_service


def create_menu(db: Session, menu_data: MenuCreate) -> MenuModel:
    return menu_service.create_menu(db, menu_data)


def get_menus(db: Session, is_available: Optional[bool] = None) -> List[MenuModel]:
    return menu_service.fetch_menus(db, is_available=is_available)


def get_menu_by_id(db: Session, menu_id: int) -> MenuModel:
    return menu_service.fetch_menu_by_id(db, menu_id)


def update_menu(db: Session, menu_id: int, menu_data: MenuUpdate) -> MenuModel:
    return menu_service.update_menu(db, menu_id, menu_data)


def update_menu_availability(db: Session, menu_id: int, is_available: bool) -> MenuModel:
    return menu_service.update_menu_availability(db, menu_id, is_available)


def delete_menu(db: Session, menu_id: int) -> None:
    menu_service.soft_delete_menu(db, menu_id)
