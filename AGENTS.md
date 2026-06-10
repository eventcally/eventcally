# AGENTS.md

Primary agent instructions live in [`.github/copilot-instructions.md`](.github/copilot-instructions.md). Read that first. This file supplements it with operational details.

## Lint order matters

Run in this order — each step may change files the next expects:
```
isort . && black . && flake8 && lint-imports && python .scripts/module_import_whitelist.py project/domain project/application
```
Or just: `pre-commit run --all-files` (runs all hooks in the correct order).

## Import layering (strict)

Enforced by `.importlinter` and the whitelist scripts:
- **`project/domain/`** — only stdlib, typing, pydantic, abc, datetime, enum, dateutil, pytz. Cannot import application or infrastructure.
- **`project/application/`** — only stdlib, typing, pydantic, abc, datetime, enum, logging, itertools + domain. Cannot import infrastructure.
- **`project/infrastructure/`** — can import application and domain.

Violations fail `lint-imports`. Check both files before adding imports:
- `.importlinter`
- `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`

## Tests

- `tests/application/` and `tests/domain/` run without external dependencies.
- All other tests (views, api, infrastructure, service_layer) require PostGIS + Redis. Use `docker-compose -f docker-compose.test.services.yml up -d` for local testing.
- Run a single test: `pytest tests/views/test_event.py::TestEventView::test_create -v`
- Key fixtures: `app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus` (see `tests/conftest.py`).
- Test base classes in `tests/base_test.py` — use these for view tests instead of writing boilerplate.

## Adding new DDD commands/events

Templates with scaffolding guides exist in `.github/prompts/`:
- `.github/prompts/add-ddd-command.prompt.md` — step-by-step command + handler creation
- `.github/prompts/add-ddd-event.prompt.md` — step-by-step event + handler creation

Key points:
- Commands go in `project/application/commands/`, handlers in `project/application/command_handlers/`.
- Register new handlers in the DI container (`project/container.py`) via `FactoryAggregate`.
- New Celery tasks must be imported in `project/celery_tasks.py`.
- Commands are Pydantic models (`Command` or `CommandWithResult[T]`). The `actor` field is auto-added.

## Code generation

- SQLAlchemy models have `*_generated.py` files generated from YAML schemas in `codegen/config/`.
- **Never edit `*_generated.py`.** Put custom logic in the handwritten sibling file (e.g., `event.py` extends `event_generated.py`).
- Regenerate: `python codegen/generate.py`

## Environment

- Entry point: `bootstrap.py` (set via `FLASK_APP=.flaskenv`).
- Dev server: `flask run --host 0.0.0.0`.
- Docker Compose (`docker-compose up --build`) runs everything: PostGIS, Redis, Mailhog, Flask, Celery worker/beat, Flower.
- Required env vars: `DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings. See `doc/development.md` for full list.

## Common gotchas

- PostGIS migration diffs sometimes need manual correction after `flask db migrate`.
- Deferred SQLAlchemy columns may require explicit `undefer()` in query options.
- `isort` skips `*_generated.py` files — don't fight it.
- flake8 ignores E501 (line length) — Black handles formatting.
