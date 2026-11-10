from typing import List

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.dish_model import DishModel
from app.models.menu_model import MenuModel
from app.schemas.menu_schema import MenuCreate


def fetch_dishes_by_ids(db: Session, dish_ids: list[int]) -> List[DishModel]:
    unique_ids = set(dish_ids)
    dishes = (
        db.query(DishModel)
        .filter(DishModel.id.in_(unique_ids), DishModel.deleted_at.is_(None))
        .all()
    )
    missing_ids = unique_ids - {dish.id for dish in dishes}
    if missing_ids:
        missing_text = ", ".join(str(dish_id) for dish_id in sorted(missing_ids))
        raise NotFoundError(f"No existen los platos con id: {missing_text}")
    return dishes


def create_menu(db: Session, menu_data: MenuCreate) -> MenuModel:
    menu = MenuModel(
        name=menu_data.name,
        type=menu_data.type,
        price=menu_data.price,
        dishes=fetch_dishes_by_ids(db, menu_data.dish_ids),
    )
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu


def fetch_menus(db: Session) -> List[MenuModel]:
    return (
        db.query(MenuModel)
        .filter(MenuModel.deleted_at.is_(None))
        .all()
    )


def fetch_menu_by_id(db: Session, menu_id: int) -> MenuModel:
    menu = (
        db.query(MenuModel)
        .filter(MenuModel.id == menu_id, MenuModel.deleted_at.is_(None))
        .first()
    )
    if menu is None:
        raise NotFoundError("El menú no existe")
    return menu

