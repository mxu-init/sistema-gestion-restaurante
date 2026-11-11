"""Step definitions for the SGR-49 Gherkin scenarios."""

from __future__ import annotations

import uuid

from pytest_bdd import given, parsers, then, when
from sqlalchemy import text

from app.models import CategoryModel


@given("the SGR-49 application is available")
def sgr_49_application_is_available(app_client) -> None:
    """The real application factory is ready for an HTTP scenario."""
    assert app_client is not None


@given("a test-only crash route is registered")
def test_only_crash_route_is_registered(crash_client) -> None:
    """A second application instance exposes the crash route only for this test."""
    assert crash_client is not None


@given("a PostgreSQL integration route is available")
def postgresql_integration_route_is_available(db_client) -> None:
    """The database scenario uses a test-only route over the local PostgreSQL session."""
    assert db_client is not None


@when("the client requests the missing demo resource 41")
def request_missing_demo_resource(app_client, bdd_state: dict) -> None:
    bdd_state["response"] = app_client.get("/errores-demo/no-encontrado/41")


@when("the client submits a demo reservation without a name")
def submit_reservation_without_name(app_client, bdd_state: dict) -> None:
    bdd_state["response"] = app_client.post(
        "/errores-demo/validacion",
        json={"comensales": 2},
    )


@when("the client requests the test-only crash route")
def request_crash_route(crash_client, bdd_state: dict) -> None:
    bdd_state["response"] = crash_client.get("/__bdd/crash")


@when(parsers.parse('the client calls health with correlation id "{correlation_id}"'))
def call_health_with_correlation_id(app_client, bdd_state: dict, correlation_id: str) -> None:
    bdd_state["response"] = app_client.get(
        "/health",
        headers={"X-Request-ID": correlation_id},
    )


@when("the client calls health without a correlation id")
def call_health_without_correlation_id(app_client, bdd_state: dict) -> None:
    bdd_state["response"] = app_client.get("/health")


@when("the client creates the same category twice")
def create_same_category_twice(db_client, bdd_state: dict) -> None:
    category_name = f"BddCat_{uuid.uuid4().hex[:8]}"
    bdd_state["created_names"].append(category_name)
    payload = {"name": category_name}
    bdd_state["first_response"] = db_client.post("/integration/categories", json=payload)
    bdd_state["response"] = db_client.post("/integration/categories", json=payload)


@then(parsers.parse("the response status is {status_code:d}"))
def response_status_is(bdd_state: dict, status_code: int) -> None:
    assert bdd_state["response"].status_code == status_code


@then(parsers.parse('the response detail is "{detail}"'))
def response_detail_is(bdd_state: dict, detail: str) -> None:
    body = bdd_state["response"].json()
    assert list(body.keys()) == ["detail"]
    assert body["detail"] == detail


@then("the response body hides internal exception details")
def response_hides_internal_details(bdd_state: dict) -> None:
    raw_body = bdd_state["response"].text.lower()
    assert "traceback" not in raw_body
    assert "runtimeerror" not in raw_body
    assert "supersecret" not in raw_body
    assert "postgresql" not in raw_body


@then(parsers.parse('the response correlation id is "{correlation_id}"'))
def response_correlation_id_is(bdd_state: dict, correlation_id: str) -> None:
    assert bdd_state["response"].headers.get("X-Request-ID") == correlation_id


@then("the response includes a generated correlation id")
def response_includes_generated_correlation_id(bdd_state: dict) -> None:
    correlation_id = bdd_state["response"].headers.get("X-Request-ID")
    assert isinstance(correlation_id, str)
    assert correlation_id.strip() != ""


@then("the duplicate response status is 409")
def duplicate_response_status_is_409(bdd_state: dict) -> None:
    assert bdd_state["first_response"].status_code == 201
    assert bdd_state["response"].status_code == 409


@then("the duplicate detail is the Spanish uniqueness message without SQL leakage")
def duplicate_detail_is_spanish_without_sql(bdd_state: dict) -> None:
    response = bdd_state["response"]
    body = response.json()
    assert list(body.keys()) == ["detail"]
    assert body["detail"] == "Ya existe una categoría con ese nombre"
    lowered = response.text.lower()
    for token in ("23505", "insert into", "sqlstate", "categories", "integrityerror"):
        assert token not in lowered


@then("the same database session can still execute a query")
def same_session_can_execute_a_query(db_session) -> None:
    assert db_session.execute(text("SELECT 1")).scalar_one() == 1
    saved = (
        db_session.query(CategoryModel)
        .filter(CategoryModel.name.like("BddCat_%"))
        .count()
    )
    assert saved >= 1
