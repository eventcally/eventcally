# CLAUDE.md

Guidance for Claude when working in this repository.

> **Read first:** [`.github/copilot-instructions.md`](.github/copilot-instructions.md) is the
> primary agent instruction file, and [`AGENTS.md`](AGENTS.md) supplements it with
> operational details. This file complements both — it does not replace them. When in
> doubt, those two win.

## Project Overview

**EventCally** is a Flask + SQLAlchemy **event-calendar platform** built with
**Domain-Driven Design**. It serves a server-rendered web UI plus a REST API, runs
background work on Celery, and stores geo data in PostgreSQL/PostGIS.

## Tech Stack

- **Runtime**: Python 3.12 (`.python-version`; 3.11 for pre-commit hook envs); deps in `pyproject.toml` + `uv.lock`, managed by uv; venv in `.venv/`
- **Web**: Flask 3 (Flask-SQLAlchemy, Flask-Migrate, Flask-Security-Too, Flask-Admin, Flask-RESTful, flask-apispec)
- **Architecture**: DDD with a `dependency-injector` container; layering enforced by `import-linter`
- **Tasks**: Celery 5 (Redis broker, celery beat, Flower)
- **DB**: PostgreSQL + PostGIS via psycopg2 + SQLAlchemy 2 + GeoAlchemy2; Alembic migrations
- **Serialization / commands**: marshmallow (API), pydantic (commands)
- **Rate limiting**: Flask-Limiter (own `LIMITER_REDIS_URL`)
- **Server**: gunicorn
- **Tests**: pytest (pytest-split, pytest-cov, pytest-mock); Playwright e2e
- **Lint/format**: isort, black, flake8, import-linter, pre-commit
- **Other**: Babel (i18n), icalendar/recurring-ical-events, googlemaps, Authlib/Flask-Dance (OAuth)

## Commands

```bash
# Setup
uv sync                                        # creates .venv with runtime + dev deps
source .venv/bin/activate                      # or prefix commands with `uv run`

# Run locally (needs DATABASE_URL, SECRET_KEY, SERVER_NAME, REDIS_URL,
#              LIMITER_REDIS_URL, GOOGLE_MAPS_API_KEY, mail settings)
flask db upgrade
flask run --host 0.0.0.0
docker-compose up --build                      # full stack: PostGIS, Redis, Mailhog, Flask, Celery, Flower

# Test — dockerized, no host Postgres/Redis/venv needed (`pytest tests/unit` needs no services)
./runtests.sh                                  # full parallel suite + coverage, in Docker
# Subset/single test: pass paths after `--`. Needs a group, which creates that group's
# database and exports TEST_DATABASE_URL — plain `run --rm pytest pytest <path>` fails
# with `could not translate host name "myserver"`.
./runtests.sh --splits 1 --group 1 -- tests/integration/presentation/web/views/test_event.py::test_create_allday -v --no-cov
npm install && npx playwright test             # e2e

# Regenerate model/repo code after editing .scripts/codegen/config/*.yaml
python .scripts/codegen/generate.py

# Lint / format — order matters, run before commit
pre-commit run --all-files
# equivalently:
isort . && black . && flake8 && lint-imports && \
  python .scripts/module_import_whitelist.py project/domain project/application
```

## Structure

- `project/` — the composition root: `factory.py` (`create_app`; `__init__.py` is empty), `config.py`, DI (`container.py`) and the `celery.py` worker entrypoint; the delivery code lives in `project/presentation/` (web, api, cli, `tasks/` for Celery tasks), Flask extensions/Celery app/OAuth2 server/`init_data` in `project/infrastructure/`
- `project/shared/` — cross-**layer** helpers (`utils`, `dateutils`, `imageutils`, `context`, `feature_flags`); a leaf that may import only the domain
- `project/domain/` — models, abstract interfaces, business logic (**no** application/infrastructure imports)
- `project/application/` — pydantic commands, command/event handlers, `message_bus.py`, read models
- `project/services/` — only `cache`, `dump`, `seo`; no ORM read/write services (settings are read via `GetSettingsQuery`; `upsert_settings` lives in `infrastructure/init_data.py`)
- `project/infrastructure/user_datastore.py` — the Flask-Security datastore adapter (users, roles, ToS); imports no models
- `project/infrastructure/seed_helpers.py` — fixture-only ORM helpers for `presentation/cli/test.py` and `tests/integration/seeder.py`; never import from presentation/application
- `project/infrastructure/` — concrete adapters (SQLAlchemy repos, Celery dispatchers, external services), plus the ORM `models/` (codegen output), Alembic `migrations/` and `dbtypes.py`
- `project/presentation/` — the delivery layer, split by channel:
  - `web/` — server-rendered site: `views/`, `modular/` (the shared modular CRUD view framework), `forms/`, `templates/`, `static/`, `jinja_filters.py`
  - `api/` — REST resources + marshmallow schemas (flat; the version lives in the `/api/v1` URL prefix)
  - `cli/` — Flask CLI commands (outside the read-path contract: `cli/test.py` is a dev/e2e fixture CLI)
  - `shared/` — cross-**channel** helpers (`access`, `permissions`, `oauth2_extensions`, `query_args`, `query_results`, `current_admin_unit`, `scopes`, `rate_limit`, `urls`)
- `project/templates/email/` — e-mail templates; they stay outside `presentation/web` because infrastructure renders them (also from Celery). Flask loads both template roots through a `ChoiceLoader`
- `.scripts/codegen/` — `generate.py` + YAML schemas in `.scripts/codegen/config/`
- `tests/` — `unit/` (no services: domain, application, pure helpers) and `integration/` (PostGIS + Redis; holds `conftest.py`, `base_test.py`, `seeder.py`). **Tests mirror the source tree**: the tests of `project/presentation/web/views/event.py` live in `tests/integration/presentation/web/views/test_event.py`
- `e2e/`, `doc/`, `deployment/`, `.scripts/`

**Flow:** reads: view / API → `query_bus` → query handler → read repository (read model out); writes: view / API → `message_bus` → command handler → repository (domain via infrastructure); events dispatch through the message bus, some onto Celery.

## Patterns

- **DDD layering (strict):** `domain` ← `application` ← `infrastructure` ← `presentation`. Never import "up" a layer. Enforced by `.importlinter` (`lint-imports`) and `.scripts/module_import_whitelist.py`; allowed imports live in `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`.
- **Shared packages:** `project.shared` is shared across **layers** and is a leaf (it may import only `project.domain`). `project.presentation.shared` is shared across **channels** (web, API). Web and API never import each other (contracts `web-does-not-import-api`, `api-does-not-import-web`, `presentation-shared-is-channel-neutral`); the one exception is `views.js` → `CustomWidgetSchema`. Put a helper both channels need in `presentation/shared/`.
- **Tests mirror the source tree:** a module's tests live at the mirrored path (`tests/{unit,integration}/<path below project/>/test_<module>.py`). Fixtures stay in `tests/integration/`.
- **Commands/events:** pydantic `Command` / `CommandWithResult[T]` in `project/application/commands/`, handlers in `command_handlers/`, registered in the DI container (`project/container.py`) and driven through `message_bus.py`. The `actor` field is auto-added.
- **Read side (queries):** every read in views (incl. `web/modular`)/API goes through pydantic `Query[T]` objects in `project/application/queries/`, dispatched via `QueryBus` (`Application.cqrs.query_bus`; `BaseResource.query_bus`, `BaseView.query_bus`). Handlers in `query_handlers/` get read repos by constructor injection and return hand-written, use-case shaped read models (`read_models/`, `Page[T]` for lists). Query read repos use `infrastructure.read_session` (read-only, released after each top-level query); event-handler read repos stay on `session_factory`. Modular list and object views implement `create_list_query()` / `create_get_query()` (there is no ORM list path any more). Search criteria are pydantic models (`EventSearchCriteria`); visibility rules live in handlers/services (`EventVisibilityService`). Access decisions use the same permission policy (`project/presentation/shared/access.py` is a thin wrapper; API decorators take a `ResourceKind`). Scaffold: `.github/prompts/add-ddd-query.prompt.md`; reference implementation: event organizers (`ListEventOrganizersQuery`, `SqlAlchemyEventOrganizerReadRepository`). Query handlers for private data authorize the actor via `ActorAuthorizationService` (same rule as commands, `actor_permission_policy`); reference: organization invitations (`ListOrganizationInvitationsQuery`).
- **Import ratchet:** the `delivery-reads-through-queries` contract in `.importlinter` forbids `project.presentation.web` / `project.presentation.api` / `project.presentation.shared` → `project.infrastructure.models` (`presentation.cli` is outside), with an `ignore_imports` list that only holds the permanent exemption `presentation.web.views.flask_admin` (Flask-Admin stays ORM; Flask-Security `current_user` and Authlib stay too). Regenerate with `python .scripts/models_import_ignores.py --write` after removing imports; never add entries by hand. Progress: `python .scripts/read_path_report.py`.
- **Generated code:** `*_generated.py` is generated from `.scripts/codegen/config/` YAML — **never edit it**. Put custom logic in the handwritten sibling (e.g. `event.py` extends `event_generated.py`). isort/flake8 already skip these files.
- **Data access:** SQLAlchemy ORM through repositories; deferred columns may need explicit `undefer()`.
- **Tests:** reuse fixtures from `tests/integration/conftest.py` (`app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus`) and base classes in `tests/integration/base_test.py`; assert through the message bus / repositories, not around the architecture.

## Pitfalls

- New Celery tasks must be imported/registered in `project/presentation/tasks/celery_tasks.py`.
- Celery task names are a wire contract: every `@celery.task` passes an explicit `name=`; never rename it or derive it from `__name__`. New tasks use `project.<module path>.<func>` of their real module; the frozen set lives in `tests/integration/infrastructure/test_celery_app.py`.
- E-mail templates stay in `project/templates/email/` and import the web macros (`_macros.html`); Flask resolves both roots (`presentation/web/templates`, then `project/templates`) via a `ChoiceLoader` set in `create_app`. `babel.cfg` lists both.
- `project/translations/` stays in `project/` (Flask-Babel resolves it from `app.root_path`).
- `presentation/cli` is outside the read-path contract (it writes fixtures through the ORM via `infrastructure/seed_helpers.py`).
- Query handlers must return materialized read models; the read session is closed when the bus returns, so lazy loads fail. The read session only sees committed data.
- PostGIS migration diffs from `flask db migrate` sometimes need manual correction — always review before `upgrade`.
- flake8 ignores E501/E203/E711 (Black owns formatting); don't fight isort skipping `*_generated.py`.
- Never hand-edit `uv.lock`: use `uv add <pkg>` / `uv add --dev <pkg>` / `uv lock --upgrade-package <pkg>`. CI and Docker run `uv sync --locked`, so commit `uv.lock` together with `pyproject.toml`. `setuptools` stays pinned (jsonschema 3.2.0 needs `pkg_resources`).
- Required env vars for running: `DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings (see `doc/development.md`).

## Key Files

- Bootstrap/wiring: `project/factory.py`, `project/config.py`, `bootstrap.py` (`FLASK_APP` set in `.flaskenv`)
- DI container: `project/container.py`
- Message bus: `project/application/message_bus.py`
- Commands / handlers: `project/application/commands/`, `project/application/command_handlers/`
- API wiring: `project/presentation/api/__init__.py`
- Cross-layer / cross-channel helpers: `project/shared/`, `project/presentation/shared/`
- Tasks: `project/presentation/tasks/celery_tasks.py`, `project/infrastructure/celery_base_tasks.py`
- Codegen: `.scripts/codegen/generate.py`, `.scripts/codegen/config/`
- Tests: `tests/integration/conftest.py`, `tests/integration/base_test.py`, `tests/integration/seeder.py`
- CI: `.github/workflows/{lint,test,playwright}.yml`
- Docs: `doc/development.md`, `doc/deployment.md`
