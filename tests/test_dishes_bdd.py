from decimal import Decimal
import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.models.category_model import CategoryModel
from app.models.dish_model import DishModel

scenarios("features/dishes.feature")


@pytest.fixture
def context():
    return {}


# --- Dado ---

@given("que existen platos registrados en el restaurante")
def existing_dishes(test_db: Session, context):
    category = test_db.query(CategoryModel).first()
    dish1 = DishModel(name="Gazpacho Andaluz", price=Decimal("6.00"), category_id=category.id, is_available=True)
    dish2 = DishModel(name="Tortilla Española", price=Decimal("7.50"), category_id=category.id, is_available=True)
    test_db.add_all([dish1, dish2])
    test_db.commit()
    test_db.refresh(dish1)
    test_db.refresh(dish2)
    context["dish_ids"] = [dish1.id, dish2.id]


@given(parsers.parse('que existe un plato con nombre "{name}" y precio {price:f}'))
def dish_with_name_and_price(test_db: Session, context, name: str, price: float):
    category = test_db.query(CategoryModel).first()
    dish = DishModel(name=name, price=Decimal(str(price)), category_id=category.id, is_available=True)
    test_db.add(dish)
    test_db.commit()
    test_db.refresh(dish)
    context["current_dish"] = dish


@given("que no existe ningún plato con id 999999")
def no_dish_with_id():
    pass


@given(parsers.parse('que existe una categoría "{category_name}"'))
def category_exists(test_db: Session, context, category_name: str):
    category = test_db.query(CategoryModel).filter(CategoryModel.name == category_name).first()
    if not category:
        category = CategoryModel(name=category_name)
        test_db.add(category)
        test_db.commit()
        test_db.refresh(category)
    context["category"] = category


@given(parsers.parse('que existe un plato con nombre "{name}"'))
def dish_to_delete(test_db: Session, context, name: str):
    category = test_db.query(CategoryModel).first()
    dish = DishModel(name=name, price=Decimal("10.00"), category_id=category.id, is_available=True)
    test_db.add(dish)
    test_db.commit()
    test_db.refresh(dish)
    context["current_dish"] = dish


# --- Cuando ---

@when("consulto la lista de platos")
def get_all_dishes(client: TestClient, context):
    context["response"] = client.get("/dishes/")


@when("consulto el plato por su identificador")
def get_dish_by_id(client: TestClient, context):
    dish_id = context["current_dish"].id
    context["response"] = client.get(f"/dishes/{dish_id}")


@when("consulto el plato con id 999999")
def get_nonexistent_dish(client: TestClient, context):
    context["response"] = client.get("/dishes/999999")


@when(parsers.parse('solicito crear un plato con nombre "{name}" y precio {price:f} en la categoría "{category_name}"'))
def create_dish(client: TestClient, context, name: str, price: float, category_name: str):
    category = context.get("category")
    data = {
        "name": name,
        "price": str(price),
        "category_id": str(category.id),
        "is_available": "true",
    }
    context["response"] = client.post("/dishes/", data=data)


@when("solicito eliminar el plato")
def delete_dish(client: TestClient, context):
    dish_id = context["current_dish"].id
    context["response"] = client.delete(f"/dishes/{dish_id}")


# --- Entonces ---

@then(parsers.parse("la respuesta tiene código {status_code:d}"))
def check_status_code(context, status_code: int):
    assert context["response"].status_code == status_code


@then("la lista contiene los platos registrados")
def check_dishes_list(context):
    data = context["response"].json()
    assert isinstance(data, list)
    returned_ids = {d["id"] for d in data}
    for did in context["dish_ids"]:
        assert did in returned_ids


@then(parsers.parse('el detalle del plato muestra el nombre "{expected_name}"'))
def check_dish_detail(context, expected_name: str):
    data = context["response"].json()
    assert data["name"] == expected_name


@then(parsers.parse('el plato creado tiene el nombre "{expected_name}"'))
def check_created_dish(context, expected_name: str):
    data = context["response"].json()
    assert data["name"] == expected_name


@then("el plato no aparece en las consultas posteriores")
def check_dish_not_found(client: TestClient, context):
    dish_id = context["current_dish"].id
    res = client.get(f"/dishes/{dish_id}")
    assert res.status_code == 404

