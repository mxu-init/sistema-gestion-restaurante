from decimal import Decimal
import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models.category_model import CategoryModel
from app.models.dish_model import DishModel
from app.models.menu_model import MenuModel

scenarios("features/menus.feature")


@pytest.fixture
def context():
    return {}


# --- Dado ---

@given("que existen platos disponibles en la carta")
def dishes_available(test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    d1 = DishModel(name="Ensalada Mixta", price=Decimal("7.00"), category_id=category.id, is_available=True)
    d2 = DishModel(name="Solomillo al Whisky", price=Decimal("15.00"), category_id=category.id, is_available=True)
    test_db.add_all([d1, d2])
    test_db.commit()
    test_db.refresh(d1)
    test_db.refresh(d2)
    context["dishes"] = [d1, d2]
    context["dish_ids"] = [d1.id, d2.id]


@given("que no existe ningún plato con id 999999")
def no_dish_999999():
    pass


@given("que no existe el menú con id 999999")
def no_menu_999999():
    pass


@given(parsers.parse('que existe un menú "{menu_name}" con precio {price:f}'))
def menu_with_name_and_price(test_db: Session, context, menu_name: str, price: float):
    category = test_db.query(CategoryModel).first()
    d1 = DishModel(name=f"Plato para {menu_name}", price=Decimal("8.00"), category_id=category.id, is_available=True)
    test_db.add(d1)
    test_db.commit()
    test_db.refresh(d1)

    menu = MenuModel(
        name=menu_name,
        type="estándar",
        day="Lunes",
        price=Decimal(str(price)),
        is_available=True,
        dishes=[d1],
    )
    test_db.add(menu)
    test_db.commit()
    test_db.refresh(menu)
    context["current_menu"] = menu
    context["menu_dish"] = d1


@given("que existe un menú activo disponible")
def active_available_menu(test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    d1 = DishModel(name="Plato Menú Activo", price=Decimal("9.00"), category_id=category.id, is_available=True)
    test_db.add(d1)
    test_db.commit()
    test_db.refresh(d1)

    menu = MenuModel(
        name="Menú Activo",
        type="estándar",
        day="Martes",
        price=Decimal("18.00"),
        is_available=True,
        dishes=[d1],
    )
    test_db.add(menu)
    test_db.commit()
    test_db.refresh(menu)
    context["current_menu"] = menu


@given("que existe un menú compuesto por platos disponibles")
def menu_with_available_dishes(test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    d1 = DishModel(name="Plato Menú Compuesto", price=Decimal("11.00"), category_id=category.id, is_available=True)
    test_db.add(d1)
    test_db.commit()
    test_db.refresh(d1)

    menu = MenuModel(
        name="Menú Compuesto",
        type="del día",
        day="Miércoles",
        price=Decimal("14.00"),
        is_available=True,
        dishes=[d1],
    )
    test_db.add(menu)
    test_db.commit()
    test_db.refresh(menu)
    context["current_menu"] = menu
    context["dish_to_deactivate"] = d1


@given("que existen menús disponibles y menús no disponibles")
def menus_available_and_unavailable(test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    d_ok = DishModel(name="Plato Disponible", price=Decimal("5.00"), category_id=category.id, is_available=True)
    d_off = DishModel(name="Plato No Disponible", price=Decimal("5.00"), category_id=category.id, is_available=False)
    test_db.add_all([d_ok, d_off])
    test_db.commit()
    test_db.refresh(d_ok)
    test_db.refresh(d_off)

    m_avail = MenuModel(name="Menú Disponible", type="del día", price=Decimal("12.00"), is_available=True, dishes=[d_ok])
    m_unavail = MenuModel(name="Menú No Disponible", type="del día", price=Decimal("12.00"), is_available=True, dishes=[d_off])
    test_db.add_all([m_avail, m_unavail])
    test_db.commit()
    test_db.refresh(m_avail)
    test_db.refresh(m_unavail)
    context["avail_menu_id"] = m_avail.id
    context["unavail_menu_id"] = m_unavail.id


@given(parsers.parse('que existe un menú "{menu_name}"'))
def menu_to_delete(test_db: Session, context, menu_name: str):
    category = test_db.query(CategoryModel).first()
    d = DishModel(name=f"Plato de {menu_name}", price=Decimal("7.00"), category_id=category.id, is_available=True)
    test_db.add(d)
    test_db.commit()
    test_db.refresh(d)

    menu = MenuModel(name=menu_name, type="estándar", price=Decimal("15.00"), is_available=True, dishes=[d])
    test_db.add(menu)
    test_db.commit()
    test_db.refresh(menu)
    context["current_menu"] = menu


@given("que existe un menú que ya ha sido eliminado")
def menu_already_deleted(client: TestClient, test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    d = DishModel(name="Plato Menú Pre-borrado", price=Decimal("7.00"), category_id=category.id, is_available=True)
    test_db.add(d)
    test_db.commit()
    test_db.refresh(d)

    menu = MenuModel(name="Menú Ya Borrado", type="estándar", price=Decimal("15.00"), is_available=True, dishes=[d])
    test_db.add(menu)
    test_db.commit()
    test_db.refresh(menu)
    context["current_menu"] = menu

    # Delete once via API
    del_res = client.delete(f"/menus/{menu.id}")
    assert del_res.status_code == 204


# --- Cuando ---

@when(parsers.parse('creo un menú con nombre "{name}", precio {price:f} y día "{day}"'))
def create_menu_valid(client: TestClient, context, name: str, price: float, day: str):
    payload = {
        "name": name,
        "type": "del día",
        "day": day,
        "price": price,
        "dish_ids": context["dish_ids"],
    }
    context["response"] = client.post("/menus", json=payload)


@when("intento crear un menú con el plato inexistente 999999")
def create_menu_nonexistent_dish(client: TestClient, context):
    payload = {
        "name": "Menú Inválido",
        "type": "del día",
        "price": 15.00,
        "dish_ids": [999999],
    }
    context["response"] = client.post("/menus", json=payload)


@when(parsers.parse("intento crear un menú con precio negativo {price:f}"))
def create_menu_negative_price(client: TestClient, context, price: float):
    payload = {
        "name": "Menú Precio Negativo",
        "type": "del día",
        "price": price,
        "dish_ids": context["dish_ids"],
    }
    context["response"] = client.post("/menus", json=payload)


@when("consulto el menú por su identificador")
def get_menu_by_id(client: TestClient, context):
    menu_id = context["current_menu"].id
    context["response"] = client.get(f"/menus/{menu_id}")


@when("consulto el menú con id 999999")
def get_nonexistent_menu(client: TestClient, context):
    context["response"] = client.get("/menus/999999")


@when(parsers.parse('modifico el menú con nuevo nombre "{name}" y precio {price:f}'))
def update_menu_name_and_price(client: TestClient, context, name: str, price: float):
    menu_id = context["current_menu"].id
    payload = {
        "name": name,
        "price": price,
    }
    context["response"] = client.patch(f"/menus/{menu_id}", json=payload)


@when("desactivo manualmente la disponibilidad del menú")
def update_availability_to_false(client: TestClient, context):
    menu_id = context["current_menu"].id
    payload = {"is_available": False}
    context["response"] = client.patch(f"/menus/{menu_id}/availability", json=payload)


@when("desactivo uno de los platos que componen el menú")
def deactivate_menu_dish(client: TestClient, test_db: Session, context):
    dish = context["dish_to_deactivate"]
    dish.is_available = False
    test_db.commit()


@when("solicito listar los menús filtrando por disponibles")
def list_available_menus(client: TestClient, context):
    context["response"] = client.get("/menus?is_available=true")


@when("solicito eliminar el menú por su identificador")
def delete_menu_by_id(client: TestClient, context):
    menu_id = context["current_menu"].id
    context["response"] = client.delete(f"/menus/{menu_id}")


@when("solicito eliminar nuevamente ese mismo menú")
def delete_menu_again(client: TestClient, context):
    menu_id = context["current_menu"].id
    context["response"] = client.delete(f"/menus/{menu_id}")


# --- Entonces ---

@then(parsers.parse("la respuesta tiene código {status_code:d}"))
def check_status_code(context, status_code: int):
    assert context["response"].status_code == status_code


@then(parsers.parse('el menú tiene el nombre "{expected_name}" y precio {expected_price:f}'))
def check_menu_name_and_price(context, expected_name: str, expected_price: float):
    data = context["response"].json()
    assert data["name"] == expected_name
    assert Decimal(str(data["price"])) == Decimal(str(expected_price))


@then("el menú tiene disponibilidad efectiva true")
def check_effective_availability_true(context):
    data = context["response"].json()
    assert data["is_available"] is True


@then("el menú tiene disponibilidad efectiva false")
def check_effective_availability_false(context):
    data = context["response"].json()
    assert data["is_available"] is False


@then("el mensaje de error indica que no existen los platos")
def check_error_message_nonexistent_dish(context):
    data = context["response"].json()
    assert "no existen los platos" in data["detail"].lower()


@then(parsers.parse('los datos del menú corresponden a "{expected_name}"'))
def check_menu_corresponds(context, expected_name: str):
    data = context["response"].json()
    assert data["name"] == expected_name


@then(parsers.parse('el menú actualizado tiene nombre "{expected_name}" y precio {expected_price:f}'))
def check_updated_menu(context, expected_name: str, expected_price: float):
    data = context["response"].json()
    assert data["name"] == expected_name
    assert Decimal(str(data["price"])) == Decimal(str(expected_price))


@then("la consulta del menú refleja que su disponibilidad efectiva es false")
def check_menu_get_availability_false(client: TestClient, context):
    menu_id = context["current_menu"].id
    res = client.get(f"/menus/{menu_id}")
    assert res.status_code == 200
    assert res.json()["is_available"] is False


@then("la bandera en base de datos del menú sigue activa")
def check_raw_db_is_available_true(test_db: Session, context):
    menu_id = context["current_menu"].id
    db_menu = test_db.query(MenuModel).filter(MenuModel.id == menu_id).first()
    assert db_menu.is_available is True


@then("la lista devuelta contiene únicamente menús disponibles")
def check_only_available_menus(context):
    data = context["response"].json()
    assert isinstance(data, list)
    assert any(m["id"] == context["avail_menu_id"] for m in data)
    assert not any(m["id"] == context["unavail_menu_id"] for m in data)
    for m in data:
        assert m["is_available"] is True


@then("el menú ya no aparece al consultarlo por su identificador")
def check_deleted_menu_404(client: TestClient, context):
    menu_id = context["current_menu"].id
    res = client.get(f"/menus/{menu_id}")
    assert res.status_code == 404


@then("el mensaje de error indica que el menú ya ha sido eliminado")
def check_error_message_already_deleted(context):
    data = context["response"].json()
    assert "ya ha sido eliminado" in data["detail"].lower()

