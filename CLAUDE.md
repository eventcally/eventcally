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

- **Runtime**: Python (3.12 in CI, 3.11 for pre-commit); venv in `venv/`
- **Web**: Flask 3 (Flask-SQLAlchemy, Flask-Migrate, Flask-Security-Too, Flask-Admin, Flask-RESTful, flask-apispec)
- **Architecture**: DDD with a `dependency-injector` container; layering enforced by `import-linter`
- **Tasks**: Celery 5 (Redis broker, celery beat, Flower)
- **DB**: PostgreSQL + PostGIS via psycopg2 + SQLAlchemy 2 + GeoAlchemy2; Alembic migrations
- **Serialization / commands**: marshmallow (API), pydantic (commands)
- **Rate limiting**: Flask-Limiter (own `LIMITER_REDIS_URL`)
- **Server**: gunicorn
- **Tests**: pytest (pytest-split, pytest-cov, pytest-mock); Cypress e2e
- **Lint/format**: isort, black, flake8, import-linter, pre-commit
- **Other**: Babel (i18n), icalendar/recurring-ical-events, googlemaps, Authlib/Flask-Dance (OAuth)

## Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run locally (needs DATABASE_URL, SECRET_KEY, SERVER_NAME, REDIS_URL,
#              LIMITER_REDIS_URL, GOOGLE_MAPS_API_KEY, mail settings)
flask db upgrade
./runlocal.sh                                  # flask run --host 0.0.0.0
docker-compose up --build                      # full stack: PostGIS, Redis, Mailhog, Flask, Celery, Flower

# Test (application/ + domain/ need no services; the rest need PostGIS + Redis)
docker-compose -f docker-compose.test.services.yml up -d
pytest
pytest tests/views/test_event.py::TestEventView::test_create -v   # single test
./runpytest.sh                                 # parallel split runner + coverage
npm install && ./runcypress.sh                 # e2e

# Regenerate model/repo code after editing codegen/config/*.yaml
python codegen/generate.py

# Lint / format — order matters, run before commit
pre-commit run --all-files
# equivalently:
isort . && black . && flake8 && lint-imports && \
  python .scripts/module_import_whitelist.py project/domain project/application
```

## Structure

- `project/` — Flask wiring (`__init__.py` → `create_app`), DI (`container.py`), tasks, views, forms, templates
- `project/domain/` — models, abstract interfaces, business logic (**no** application/infrastructure imports)
- `project/application/` — pydantic commands, command/event handlers, `message_bus.py`, read models
- `project/infrastructure/` — concrete adapters (SQLAlchemy repos, Celery dispatchers, external services)
- `project/api/` — REST resources + marshmallow schemas
- `codegen/` — `generate.py` + YAML schemas in `codegen/config/`
- `tests/` — mirrors source; `conftest.py`, `base_test.py`, `seeder.py`
- `cypress/`, `doc/`, `deployment/`, `.scripts/`

**Flow:** view / API → application command → handler → repository (domain via infrastructure); events dispatch through the message bus, some onto Celery.

## Patterns

- **DDD layering (strict):** `domain` ← `application` ← `infrastructure`. Never import "up" a layer. Enforced by `.importlinter` (`lint-imports`) and `.scripts/module_import_whitelist.py`; allowed imports live in `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`.
- **Commands/events:** pydantic `Command` / `CommandWithResult[T]` in `project/application/commands/`, handlers in `command_handlers/`, registered in the DI container (`project/container.py`) and driven through `message_bus.py`. The `actor` field is auto-added.
- **Generated code:** `*_generated.py` is generated from `codegen/config/` YAML — **never edit it**. Put custom logic in the handwritten sibling (e.g. `event.py` extends `event_generated.py`). isort/flake8 already skip these files.
- **Data access:** SQLAlchemy ORM through repositories; deferred columns may need explicit `undefer()`.
- **Tests:** reuse fixtures from `tests/conftest.py` (`app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus`) and base classes in `tests/base_test.py`; assert through the message bus / repositories, not around the architecture.

## Pitfalls

- New Celery tasks must be imported/registered in `project/celery_tasks.py`.
- PostGIS migration diffs from `flask db migrate` sometimes need manual correction — always review before `upgrade`.
- flake8 ignores E501/E203/E711 (Black owns formatting); don't fight isort skipping `*_generated.py`.
- Required env vars for running: `DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings (see `doc/development.md`).

## Key Files

- Bootstrap/wiring: `project/__init__.py`, `bootstrap.py` (`FLASK_APP` set in `.flaskenv`)
- DI container: `project/container.py`
- Message bus: `project/application/message_bus.py`
- Commands / handlers: `project/application/commands/`, `project/application/command_handlers/`
- API wiring: `project/api/__init__.py`
- Tasks: `project/celery_tasks.py`, `project/base_tasks.py`
- Codegen: `codegen/generate.py`, `codegen/config/`
- Tests: `tests/conftest.py`, `tests/base_test.py`, `tests/seeder.py`
- CI: `.github/workflows/{lint,test,cypress}.yml`
- Docs: `doc/development.md`, `doc/deployment.md`
