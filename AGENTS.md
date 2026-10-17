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
- **`project/services/`** — only `cache`, `dump`, `seo`. Flask-Security calls live in `project/user_datastore.py`; fixture-only ORM helpers in `project/cli/seed_helpers.py` (never import from views/api/application).
- **`project/infrastructure/`** — can import application and domain.

Violations fail `lint-imports`. Check both files before adding imports:
- `.importlinter`
- `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`

## Tests

- `tests/application/` and `tests/domain/` run without external dependencies.
- All other tests (views, api, infrastructure, service_layer) require PostGIS + Redis. Use `docker compose -f docker-compose.test.yml up -d --wait` for local testing, or run the full dockerized suite with `./runtests.sh`.
- Run a single test or subset: `./runtests.sh --splits 1 --group 1 -- tests/views/test_event.py::test_create_allday -v --no-cov`. The `--group` creates that group's database and exports `TEST_DATABASE_URL`; without it the run fails with `could not translate host name "myserver"`.
- Key fixtures: `app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus` (see `tests/conftest.py`).
- Test base classes in `tests/base_test.py` — use these for view tests instead of writing boilerplate.

## End-to-end tests

Playwright, in `e2e/tests/*.spec.js`. Easiest: `.scripts/run_e2e.sh [playwright args]` runs
everything in Docker (PostGIS service, throwaway `eventcally_e2e` database, app on :5000,
Chromium; `--project desktop` unless you pass one), e.g.
`.scripts/run_e2e.sh e2e/tests/event.spec.js -g "create"`. Or run `npx playwright test` on the
host against your own app; `--ui` gives a time-travel debugger.

- Every e2e test starts with `flask test reset --seed`, which **truncates every table in
  whatever `DATABASE_URL` points at**. Point it at a throwaway database before running the
  suite locally — the `DATABASE_URL` in `.env` is a real dev database.
- Pinned to `workers: 1` for the same reason: a second worker sharing the database would
  wipe another test's data mid-flight. Parallelism comes from `--shard` across CI jobs,
  each with its own postgres service.
- Fixtures are served by `.scripts/e2e_fixture_server.py`, which boots the app once instead
  of paying a ~3.8s import per `flask` call. It starts automatically and refuses to run
  against a database other than the one `DATABASE_URL` names.

## Adding new DDD commands/events

Templates with scaffolding guides exist in `.github/prompts/`:
- `.github/prompts/add-ddd-command.prompt.md` — step-by-step command + handler creation
- `.github/prompts/add-ddd-event.prompt.md` — step-by-step event + handler creation

Key points:
- Commands go in `project/application/commands/`, handlers in `project/application/command_handlers/`.
- Register new handlers in the DI container (`project/container.py`) via `FactoryAggregate`.
- New Celery tasks must be imported in `project/celery_tasks.py`.
- Commands are Pydantic models (`Command` or `CommandWithResult[T]`). The `actor` field is auto-added.

## Adding read-side queries

Reads in views, the API and `project/modular` are migrating to the query side
(plan: `.agents/plans/2026-10-13-cqrs-read-side-migration.plan.md`). Scaffold guide:
`.github/prompts/add-ddd-query.prompt.md`. Reference implementation: event organizers
(`ListEventOrganizersQuery`, `SqlAlchemyEventOrganizerReadRepository`).

- Queries (`Query[T]`, `actor` optional — the bus fills it) go in `project/application/queries/`,
  handlers in `project/application/query_handlers/`, registered in `Cqrs.query_handler_factory`.
- Handlers return hand-written, use-case shaped read models (`Page[T]` for lists) — never ORM objects.
- Query handlers for private data authorize the actor via `ActorAuthorizationService` (same rule as commands, `actor_permission_policy`); reference: organization invitations (`ListOrganizationInvitationsQuery`).
- Query-side read repos use `infrastructure.read_session` (read-only, removed after each
  top-level query). Event-handler read repos stay on `session_factory`.
- Delivery: `self.query_bus` in `BaseResource` and modular views; `@inject` +
  `Provide[Application.cqrs.query_bus]` in flat view functions. Helpers in `project/views/utils.py`:
  `page_request_from_request_args`, `abort_if_page_out_of_range`, `result_or_404`.
- The `delivery-reads-through-queries` import-linter contract only exempts `views.flask_admin`
  (Flask-Admin stays ORM); it also covers `project.access` and `project.jinja_filters`. After removing a `project.models` import, run `python .scripts/models_import_ignores.py --write`;
  never add entries by hand.

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
- Query handlers must return materialized read models; the read session is closed when the bus returns.
- `isort` skips `*_generated.py` files — don't fight it.
- flake8 ignores E501 (line length) — Black handles formatting.
