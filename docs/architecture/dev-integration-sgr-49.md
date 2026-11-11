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

## 5. Gherkin / BDD Test Separation

### Gherkin / BDD Test Separation

Gherkin tests are maintained on the dedicated local branch `test/gherkin-bdd` (`b29ba7ea69bf85efebc414b7f945a687839eb3c5`). That branch was taken from `feat/errors-handler` before the suite was removed, so it still contains the SGR-49 implementation the scenarios depend on.

This branch keeps the ordinary Pytest unit tests in `tests/test_exception_handlers.py` and the database integration tests in `tests/test_db_exceptions.py`. It no longer contains the `.feature` files, step definitions, BDD registration module, BDD-only `tests/conftest.py`, or the `pytest-bdd` dependency.

The six scenarios were verified against the integrated application on `test/gherkin-bdd`. `python -m pytest -v tests/test_sgr_49_bdd.py` reported 6 passed.

After SGR-49 is merged into `dev`, synchronize `test/gherkin-bdd` onto that updated `dev` and confirm the diff contains only BDD changes before preparing a separate BDD pull request. Do not open that pull request against the current `dev`: the branch diff would still include the SGR-49 implementation. `test/gherkin-bdd` is an ancestor of the extraction commit, so a fast-forward onto the merged `dev` would follow the removal and drop the scenarios. Restore the BDD paths from `test/gherkin-bdd` onto a branch created from the updated `dev`, re-run the six scenarios, and only then open the BDD pull request. That synchronization is not done here. Nothing was pushed.

## 6. Testing

After the Gherkin suite was removed from this branch:

| Command | Result |
|---|---|
| `python -m pytest -v tests/test_exception_handlers.py` | 11 passed, 3 warnings |
| `python -m pytest -v tests/test_db_exceptions.py` | 4 passed, 3 warnings |
| `python -m pytest -v` | 15 passed, 3 warnings |

The full suite collects 15 tests and does not include the six Gherkin scenarios. Menu registration remains covered by the OpenAPI path assertions in `tests/test_db_exceptions.py` (`/menus`, `/menus/{menu_id}`, `/menus/{menu_id}/availability`). On `test/gherkin-bdd`, `python -m pytest -v tests/test_sgr_49_bdd.py` reported 6 passed, 3 warnings.

## 7. Commits

| SHA | Message | Purpose |
|---|---|---|
| `dd47888faef0a5c63290ae14bd495000a08470ee` | `chore(integration): merge latest dev into feat/errors-handler` | Merge `ff10751` and resolve the two conflicts. |
| `f1c2d8d2685b1ac27fc8ed32f46490fc34acd6fd` | `test(api): confirm menu routes stay registered after dev merge` | OpenAPI assertion for the menu routes. |
| `aece58d4b55ad17b74242334219b7bf52456e002` | `test(bdd): add focused Gherkin scenarios for SGR-49` | Added the six scenarios. The files stay on `test/gherkin-bdd` and are removed from this branch by the extraction commit. |
| `f2b4316f8a2934845c196bf3697f95deeefe6581` | `chore(test): extract Gherkin BDD suite from SGR-49` | Remove the BDD files and `pytest-bdd==9.0.1` from this branch. |

This file was added in `082e1b13d090d5026a57731890b80c6fd2d7b90e`, `docs(integration): document dev synchronization and SGR-49 BDD coverage`.

## 8. Remaining limitations

- Applying migrations and `alembic current` were not run during the extraction. The revision graph was inspected earlier and has one head, `3190ffa0880e`.
- `menu_service` was left on its existing commit style. A uniqueness or foreign-key failure there is handled by the global SQLAlchemy handler, which translates the error and does not call `session.rollback()` itself.
- The four pre-existing uncommitted architecture-comparison documents stay unstaged. They are not part of this synchronization or the Gherkin extraction.
- The BDD pull request waits until SGR-49 is on `dev` and `test/gherkin-bdd` has been synchronized so its diff is only the BDD suite.
