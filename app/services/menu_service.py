from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import ConflictError, NotFoundError
from app.models.dish_model import DishModel
from app.models.menu_model import MenuModel
from app.schemas.menu_schema import MenuCreate, MenuUpdate


def is_menu_effectively_available(menu: MenuModel) -> bool:
    return menu.is_effectively_available


def fetch_dishes_by_ids(db: Session, dish_ids: List[int]) -> List[DishModel]:
    unique_ids = set(dish_ids)
    all_found = db.query(DishModel).filter(DishModel.id.in_(unique_ids)).all()
    found_map = {dish.id: dish for dish in all_found}

    missing_ids = sorted(unique_ids - set(found_map.keys()))
    deleted_ids = sorted(
        dish_id
        for dish_id, dish in found_map.items()
        if dish.deleted_at is not None
    )

    if missing_ids or deleted_ids:
        errors = []
        if missing_ids:
            errors.append(
                f"no existen los platos con id: {', '.join(str(i) for i in missing_ids)}"
            )
        if deleted_ids:
            errors.append(
                f"los siguientes platos están eliminados y no se pueden añadir al menú: {', '.join(str(i) for i in deleted_ids)}"
            )
        raise NotFoundError("; ".join(errors).capitalize())

    return all_found


def create_menu(db: Session, menu_data: MenuCreate) -> MenuModel:
    menu = MenuModel(
        name=menu_data.name,
        type=menu_data.type,
        day=menu_data.day,
        price=menu_data.price,
        dishes=fetch_dishes_by_ids(db, menu_data.dish_ids),
    )
    db.add(menu)
    db.commit()
    db.refresh(menu)
    return menu


def fetch_menus(db: Session, is_available: Optional[bool] = None) -> List[MenuModel]:
    menus = (
        db.query(MenuModel)
        .options(selectinload(MenuModel.dishes))
        .filter(MenuModel.deleted_at.is_(None))
        .order_by(MenuModel.id)
        .all()
    )
    if is_available is not None:
        menus = [menu for menu in menus if is_menu_effectively_available(menu) == is_available]
    return menus


def fetch_menu_by_id(db: Session, menu_id: int) -> MenuModel:
    menu = (
        db.query(MenuModel)
        .options(selectinload(MenuModel.dishes))
        .filter(MenuModel.id == menu_id, MenuModel.deleted_at.is_(None))
        .first()
    )
    if menu is None:
        raise NotFoundError("El menú no existe")
    return menu


def update_menu(db: Session, menu_id: int, menu_data: MenuUpdate) -> MenuModel:
    menu = fetch_menu_by_id(db, menu_id)
    update_data = menu_data.model_dump(exclude_unset=True)

    if "dish_ids" in update_data:
        dish_ids = update_data.pop("dish_ids")
        if dish_ids is not None:
            menu.dishes = fetch_dishes_by_ids(db, dish_ids)

    for key, value in update_data.items():
        setattr(menu, key, value)

    db.commit()
    db.refresh(menu)
    return menu


def update_menu_availability(db: Session, menu_id: int, is_available: bool) -> MenuModel:
    menu = fetch_menu_by_id(db, menu_id)
    menu.is_available = is_available
    db.commit()
    db.refresh(menu)
    return menu


def soft_delete_menu(db: Session, menu_id: int) -> None:
    menu = db.query(MenuModel).filter(MenuModel.id == menu_id).first()
    if menu is None:
        raise NotFoundError("El menú no existe")
    if menu.deleted_at is not None:
        raise ConflictError("El menú ya ha sido eliminado")

    menu.deleted_at = datetime.now(timezone.utc)
    db.commit()
