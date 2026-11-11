# `feat/errors-handler` synchronization with `dev` (SGR-49)

## 1. Purpose

`feat/errors-handler` had already been integrated with `origin/dev` at `daac6dd` (PR #9). After that, `dev` gained the menus work in PR #11 (`ff1075193f76e38d943d622d38e483e7b290cdb0`). This synchronization merges that commit into `feat/errors-handler` so SGR-49 and the menu feature share one application. `dev` itself was not modified, and nothing was pushed.

## 2. Main differences found

`origin/dev` was 5 commits ahead of the previous merge base. Those commits add menus: models, schemas, service, controller, routes, and two Alembic revisions. They also add a short `app/core/exceptions.py` (`AppError`, `NotFoundError`, `ConflictError`) and register local handlers for those two classes in `app/main.py`.

This branch already owned the full SGR-49 hierarchy in the same module, plus `create_app()`, centralized handlers, correlation IDs, and the Spanish `ErrorResponse` contract. The menu service raises `NotFoundError("...")` and `ConflictError("...")`.

## 3. Necessary corrections

| File / Component | Issue | Correction | Reason |
|---|---|---|---|
| `app/core/exceptions.py` | Add/add conflict. `dev` added a 15-line hierarchy in the same new file. | Kept the SGR-49 hierarchy. | Menu calls pass a positional message, which the SGR-49 constructors already accept. Replacing the file would drop `error_code`, headers, and the other domain classes. |
| `app/main.py` | Both sides changed application setup. `dev` registered `menu_routes` and two local exception handlers on a module-level `FastAPI()` instance. | Kept `create_app()`, lifespan, middleware, `register_exception_handlers()`, and OpenAPI setup. Registered `menu_routes.router` inside the factory. Did not copy the local handlers. | `NotFoundError` and `ConflictError` are `AppError` subclasses. `app_error_handler` already maps them to HTTP 404 and 409 with `{"detail": "..."}`. |
| `app/models/__init__.py`, `alembic/env.py`, menu modules, Alembic revisions | Incoming menu code. | Taken from `dev` without edits. | No overlapping SGR-49 change. |
| `tests/test_db_exceptions.py` | No check that menu routes survived the factory. | Assert `/menus`, `/menus/{menu_id}`, and `/menus/{menu_id}/availability` are in the OpenAPI paths. | Confirms the router is on the same application as the SGR-49 handlers. |

Alembic history is a single line. `3190ffa0880e` revises `860aa19cc500`, which revises `aacc49216385`, the previous head. `alembic heads` reports only `3190ffa0880e`. No `down_revision` was edited and no merge revision was added.

Not changed: `menu_service` still commits directly and does not use `handle_db_exceptions`. Uncaught `SQLAlchemyError` values still reach `sqlalchemy_exception_handler`. Wrapping menu writes was not required to keep the routes or the exception contract.

## 4. Final integration structure

`create_app()` builds one FastAPI app. It keeps startup reference-data seeding, static files, health routes, and the existing dish, category, allergen, test, and `/errores-demo` routers. It also includes the menu router. Exception handling stays in `register_exception_handlers()`: domain errors, HTTP exceptions, validation errors, SQLAlchemy errors, and unexpected exceptions. Menu `NotFoundError` and `ConflictError` values are handled there, not by a second pair of handlers on `app/main.py`.

## 5. Gherkin tests

Gherkin coverage was not in the branch. It is an instructor requirement for SGR-49, so `pytest-bdd==9.0.1` was added and six scenarios were written under `tests/features/sgr_49/`. Pytest loads them from `tests/test_sgr_49_bdd.py` through `pytest_bdd.scenarios`. Step definitions live in `tests/step_defs/sgr_49_steps.py` and are registered with `pytest_plugins` in `tests/conftest.py`.

The scenarios cover:

1. `NotFoundError` on `GET /errores-demo/no-encontrado/41` returns HTTP 404 and the Spanish `detail`.
2. `POST /errores-demo/validacion` without `nombre` returns HTTP 422 and `Error en el campo 'nombre': El campo es obligatorio`.
3. An incoming `X-Request-ID` is returned unchanged.
4. A request without that header receives a generated `X-Request-ID`.
5. A test-only route on a second `create_app()` instance raises `RuntimeError`; the response is HTTP 500 with `Error interno del servidor` and does not include the exception text.
6. A test-only category route uses `handle_db_exceptions` so a PostgreSQL unique violation returns HTTP 409 and the same session can still run `SELECT 1`.

Scenarios 1–5 call the real factory. Their fixture replaces only `ensure_reference_data_on_startup` so those HTTP checks do not open a database connection. Scenario 6 does not use that replacement.

`python -m pytest -v tests/test_sgr_49_bdd.py` collected 6 scenarios: 5 passed, 1 failed, and the failed scenario also errored during teardown. The failure is scenario 6: both category inserts returned HTTP 500 because the connection to `localhost:5433` timed out (`psycopg.errors.ConnectionTimeout`). The scenario was not replaced with a mock.

## 6. Testing

| Command | Result |
|---|---|
| `python -m pytest -v tests/test_exception_handlers.py` | 11 passed |
| `python -m pytest -v tests/test_db_exceptions.py` | 4 failed |
| `python -m pytest -v tests/test_sgr_49_bdd.py` | 5 passed, 1 failed, 1 error |
| `python -m pytest -v` | 16 passed, 5 failed, 1 error, 3 warnings, 90.76s |

Every failure and the teardown error is `sqlalchemy.exc.OperationalError` caused by `psycopg.errors.ConnectionTimeout` to `localhost:5433` (`::1` and `127.0.0.1`). PostgreSQL is listening on port 5432, and authentication for `sgr_user` on that port was rejected. The application settings used by the tests point at port 5433, where nothing accepted a connection. `alembic current` was not completed for the same reason. `alembic heads` was run and shows one head: `3190ffa0880e`.

There is no menu test module on `dev`. Menu registration was checked through the OpenAPI paths of `create_app()` (`/menus`, `/menus/{menu_id}`, `/menus/{menu_id}/availability`). The lifespan test that contains those assertions then failed on the same database timeout, not on a missing path.

## 7. Commits

| SHA | Message | Purpose |
|---|---|---|
| `dd47888faef0a5c63290ae14bd495000a08470ee` | `chore(integration): merge latest dev into feat/errors-handler` | Merge `ff10751` and resolve the two conflicts. |
| `f1c2d8d2685b1ac27fc8ed32f46490fc34acd6fd` | `test(api): confirm menu routes stay registered after dev merge` | OpenAPI assertion for the menu routes. |
| `aece58d4b55ad17b74242334219b7bf52456e002` | `test(bdd): add focused Gherkin scenarios for SGR-49` | Six Pytest-BDD scenarios and `pytest-bdd==9.0.1`. |

This file was added in `082e1b13d090d5026a57731890b80c6fd2d7b90e`, `docs(integration): document dev synchronization and SGR-49 BDD coverage`.

## 8. Remaining limitations

- Database exception translation, rollback against PostgreSQL, lifespan reference-data seeding, and `alembic current` were not verified here. The configured database at `localhost:5433` did not accept connections.
- Applying migrations to a database was not run. The revision graph was inspected only.
- `menu_service` was left on its existing commit style. A uniqueness or foreign-key failure there is handled by the global SQLAlchemy handler, which translates the error and does not call `session.rollback()` itself.
- The four pre-existing uncommitted architecture-comparison documents were stashed before the merge and restored afterwards. They are not part of this synchronization.
