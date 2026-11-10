from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.controllers import menu_controller
from app.core.database_connection import get_db
from app.schemas.menu_schema import MenuCreate, MenuRead, MenuUpdate

router = APIRouter(prefix="/menus", tags=["Menús"])


@router.post(
    "",
    response_model=MenuRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un menú",
    description="Crea un nuevo menú asociando platos existentes por sus ids.",
)
def create_menu(menu_data: MenuCreate, db: Session = Depends(get_db)):
    return menu_controller.create_menu(db, menu_data)


@router.get(
    "",
    response_model=List[MenuRead],
    summary="Listar menús",
    description="Devuelve todos los menús que no han sido eliminados.",
)
def read_menus(db: Session = Depends(get_db)):
    return menu_controller.get_menus(db)


@router.get(
    "/{menu_id}",
    response_model=MenuRead,
    summary="Consultar un menú",
    description="Devuelve un menú por su id, si no ha sido eliminado.",
)
def read_menu(menu_id: int, db: Session = Depends(get_db)):
    return menu_controller.get_menu_by_id(db, menu_id)


@router.patch(
    "/{menu_id}",
    response_model=MenuRead,
    status_code=status.HTTP_200_OK,
    summary="Editar un menú",
    description="Permite modificar el nombre, precio, tipo, día y la lista de platos asociados a un menú.",
)
def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    db: Session = Depends(get_db),
):
    return menu_controller.update_menu(db, menu_id, menu_data)
