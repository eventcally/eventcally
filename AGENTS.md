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
- **`project/services/`** — only `cache`, `dump`, `seo`. Flask-Security calls live in `project/infrastructure/user_datastore.py`.
- **`project/infrastructure/`** — can import application and domain. Fixture-only ORM helpers live in `project/infrastructure/seed_helpers.py` (never import from presentation/application).
- **`project/presentation/`** — top layer; delivery code split by channel: `web/` (views, modular framework, forms, templates, static, Jinja filters), `api/` (REST; token/API-key only, ignores the session cookie), `bff/` (view-shaped JSON for the Vue frontends under `/bff`, session + CSRF auth, reads via the query bus, OpenAPI generated from pydantic by `bff_route`), `cli/`, and `shared/` for helpers all channels need. `web`, `api` and `bff` must not import each other. `/api/v1` authenticates only with OAuth tokens or API keys (anonymous reads when `API_READ_ANONYM`); it ignores the session cookie. Browser clients use `/bff`. BFF routes are session-only except the `bff_public` sub-blueprint (`/bff/public`, anonymous; CSRF on writes plus a rate limit); the `public` Vite entry serves public Vue pages (`/event/<id>/report`, `/organizers/<id>`, `/organizations`, `/organizations/<id>`, `/eventdates`; its anonymous place lookups `/bff/public/places` call Google behind a shared rate limit). The `bff_manage` sub-blueprint (`/bff/manage`) is session only and every route authorizes its own use case (no blanket permission check) — it also holds the event reference writes of `/eventdates`; the `manage` Vite entry serves logged-in pages outside the admin (`/planning`, `/manage/admin_unit/<id>/custom-widgets[/create|/<id>/update]`); the `widget` entry serves the embedded custom widgets (`/custom_widget/<search|calendar>`, anonymous reads through `/bff/public/widget`).
- **`project/shared/`** — cross-layer helpers (`utils`, `dateutils`, `imageutils`, `context`, `feature_flags`); a leaf that imports only the domain. Not the same as `project/presentation/shared/` (cross-channel).

Violations fail `lint-imports`. Check both files before adding imports:
- `.importlinter`
- `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`

## Tests

- `tests/unit/` runs without external dependencies or Docker: `pytest tests/unit` (seconds).
- `tests/integration/` (`presentation/{web,api,cli,shared}`, infrastructure, service_layer, ...) requires PostGIS + Redis. Use `docker compose -f docker-compose.test.yml up -d --wait` for local testing, or run the full dockerized suite with `./runtests.sh`.
- Run a single test or subset: `./runtests.sh --splits 1 --group 1 -- tests/integration/presentation/web/views/test_event.py::test_create_allday -v --no-cov`. The `--group` creates that group's database and exports `TEST_DATABASE_URL`; without it the run fails with `could not translate host name "myserver"`.
- Key fixtures: `app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus` (see `tests/integration/conftest.py`).
- **Tests mirror the source tree**: a module's tests live at the mirrored path (`project/presentation/web/views/event.py` → `tests/integration/presentation/web/views/test_event.py`, `project/shared/utils.py` → `tests/integration/shared/test_utils.py`). Fixtures stay in `tests/integration/`.
- Test base classes in `tests/integration/base_test.py` — use these for view tests instead of writing boilerplate.

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
- New Celery tasks must be imported in `project/presentation/tasks/celery_tasks.py`.
- Celery task names are a wire contract: every `@celery.task` passes an explicit `name=`; never rename it or derive it from `__name__`. New tasks use `project.<module path>.<func>` of their real module; the frozen set lives in `tests/integration/infrastructure/test_celery_app.py`.
- Commands are Pydantic models (`Command` or `CommandWithResult[T]`). The `actor` field is auto-added.

## Adding read-side queries

Reads in views (incl. `project/presentation/web/modular`) and the API are migrating to the query side
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
  `Provide[Application.cqrs.query_bus]` in flat view functions. Helpers in `project/presentation/shared/query_results.py`:
  `page_request_from_request_args`, `abort_if_page_out_of_range`, `result_or_404`.
- The `delivery-reads-through-queries` import-linter contract only exempts `views.flask_admin`
  (Flask-Admin stays ORM); it also covers `project.presentation.shared` (access, scopes, ...), the Jinja filters and forms. After removing a `project.infrastructure.models` import, run `python .scripts/models_import_ignores.py --write`;
  never add entries by hand.

## Code generation

- SQLAlchemy models have `*_generated.py` files generated from YAML schemas in `.scripts/codegen/config/`.
- **Never edit `*_generated.py`.** Put custom logic in the handwritten sibling file (e.g., `event.py` extends `event_generated.py`).
- Regenerate: `python .scripts/codegen/generate.py`

## Environment

- Entry point: `bootstrap.py` (set via `FLASK_APP=.flaskenv`); it calls `create_app` from `project/factory.py`.
- Dev server: `flask run --host 0.0.0.0`.
- Docker Compose (`docker-compose up --build`) runs everything: PostGIS, Redis, Mailhog, Flask, Celery worker/beat, Flower.
- Required env vars: `DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings. See `doc/development.md` for full list.

## Frontend (Vue 3 + BFF)

See the "Frontend" section of `.github/copilot-instructions.md` for the rules. Workflow:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend                       # Vite dev server on :5173
VITE_DEV_SERVER_URL=http://localhost:5173 flask run  # Flask serving the shells
npm run typecheck --prefix frontend && npm test --prefix frontend && npm run build --prefix frontend
python -m project.presentation.bff.openapi > frontend/openapi.json && npm run gen:api --prefix frontend
```

## Common gotchas

- Regenerate `frontend/openapi.json` + `frontend/src/api/schema.d.ts` after changing BFF models; never hand-edit `schema.d.ts`; the SPA must not import Bootstrap CSS.

- PostGIS migration diffs sometimes need manual correction after `flask db migrate`.
- Deferred SQLAlchemy columns may require explicit `undefer()` in query options.
- Query handlers must return materialized read models; the read session is closed when the bus returns.
- `isort` skips `*_generated.py` files — don't fight it.
- flake8 ignores E501 (line length) — Black handles formatting.
