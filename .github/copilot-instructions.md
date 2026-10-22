# EventCally Agent Instructions

EventCally is a Flask + SQLAlchemy event calendar platform using Domain-Driven Design patterns.

## Agent Quickstart

- Install dependencies: `uv sync`
- Run app locally: `docker compose up --build`
- Run unit tests: `pytest`
- Run coverage tests: `pytest --cov-report=html --cov=project`
- Run parallel test script (dockerized, no host Postgres/Redis needed): `./runtests.sh`
- Run e2e tests: `npm install && npx playwright test`
- Run lint/format checks before commit: `pre-commit run --all-files`

For full environment setup, use [doc/development.md](../doc/development.md).

## Architecture Guardrails

Respect strict DDD layering:

- `project/domain/`: core business logic and abstract interfaces
- `project/application/`: commands, handlers, message bus orchestration; queries, query handlers, read models, query bus
- `project/infrastructure/`: concrete adapters (SQLAlchemy, Celery, external services), ORM `models/`, Alembic `migrations/`, `dbtypes.py`, `seed_helpers.py`
- `project/presentation/`: delivery layer on top, split by channel: `web/` (views, modular framework, forms, templates, static), `api/`, `bff/` (view-shaped JSON for the Vue frontends under `/bff`, session + CSRF auth, reads via the query bus, OpenAPI generated from pydantic by `bff_route`), `cli/`; `shared/` holds helpers all channels need. Web, API and BFF must not import each other. BFF routes are session-only except the `bff_public` sub-blueprint (`/bff/public`, anonymous; CSRF on writes plus a rate limit); the `public` Vite entry serves public Vue pages (`/event/<id>/report`, `/organizers/<id>`).
- `project/shared/`: cross-layer helpers (`utils`, `dateutils`, `imageutils`, `context`, `feature_flags`); a leaf that imports only the domain

The layering rule is enforced by [.importlinter](../.importlinter). Avoid introducing imports that violate these boundaries.

Primary integration points:

- DI container: [project/container.py](../project/container.py)
- Message bus: [project/application/message_bus.py](../project/application/message_bus.py)
- Query bus (reads): [project/application/query_bus.py](../project/application/query_bus.py)
- Query authorization: Query handlers for private data authorize the actor via `ActorAuthorizationService` (same rule as commands, `actor_permission_policy`); reference: organization invitations (`ListOrganizationInvitationsQuery`).

Reads in views (incl. `project/presentation/web/modular`) and the API go through queries: a `Query[T]` in
`project/application/queries/`, a handler in `query_handlers/` returning hand-written read
models, and a read repository on the read-only `infrastructure.read_session`. See
[add-ddd-query.prompt.md](prompts/add-ddd-query.prompt.md); the event organizer reads are
the reference implementation. The
`delivery-reads-through-queries` contract in `.importlinter` keeps delivery code from
importing `project.infrastructure.models` from new modules; its `ignore_imports` list only shrinks
(`python .scripts/models_import_ignores.py --write`).
- API wiring: [project/presentation/api/__init__.py](../project/presentation/api/__init__.py)

## Generated Code Rules

- Never edit `*_generated.py` files directly.
- Update YAML model schemas under [.scripts/codegen/config/](../.scripts/codegen/config/) and regenerate with `python .scripts/codegen/generate.py`.
- Put custom model logic in handwritten extensions (for example `event.py` extending `event_generated.py`).

## Database, Migrations, and PostGIS

- Use Postgres with PostGIS extension in both dev and test databases.
- After model changes: `flask db migrate`, then review migration, then `flask db upgrade`.
- Be careful with PostGIS-related migration diffs; they sometimes need manual correction.

## Testing Conventions

- Prefer existing fixtures and app context setup from [tests/integration/conftest.py](../tests/integration/conftest.py).
- Keep tests aligned with source structure: tests live at the mirrored path (`tests/{unit,integration}/<path below project/>/test_<module>.py`, e.g. `tests/integration/presentation/web/views/` for `project/presentation/web/views/`).
- For command/event flows, assert behavior through the message bus and repository interfaces instead of bypassing architecture.

## Frontend (Vue 3 + BFF)

- `frontend/` is one Vite + TypeScript + Vue 3 + bootstrap-vue-next project with one entry per area (`src/apps/<area>/main.ts`, registered in `vite.config.ts` and `project/presentation/web/vite.py:ENTRIES`). The build lands in `project/presentation/web/static/dist/` (gitignored); the Jinja global `vite_entry(name)` renders its tags (or the dev server's when `VITE_DEV_SERVER_URL` is set).
- Pages are shells: `layout_vue3.html` extends the Bootstrap 5 frame `layout_bs5.html` and hands the SPA its boot JSON. The SPA must not import Bootstrap CSS (the frame provides it). The old frames `layout.html` (BS4) / `layout_vue.html` (Vue 2) stay untouched; the navbar links of both frames come from `get_main_menu()`.
- BFF routes are declared with `bff_route(...)` (`project/presentation/bff/routing.py`) with pydantic query/body/response models. After changing a BFF model: `python -m project.presentation.bff.openapi > frontend/openapi.json && npm run gen:api --prefix frontend` and commit both outputs (pytest and CI check the drift). Never hand-edit `frontend/src/api/schema.d.ts`.
- The admin SPA owns `/admin/*` (catch-all shell `admin.shell`); unknown paths render the SPA's not-found page. Flask-Admin stays at `/admin/flask-admin/`. Server-rendered pages the SPA links to live in `frontend/src/shared/legacy.ts`.
- Translations: the Babel `.po` files stay the single source. Use literal `t("English msgid")` calls in `.vue`/`.ts` (dynamic keys are not extracted); `npm run i18n` turns the `.po` files into `src/locales/*.json`.

## Common Pitfalls

- New Celery tasks must be imported/registered in [project/presentation/tasks/celery_tasks.py](../project/presentation/tasks/celery_tasks.py).
- Celery task names are a wire contract: every `@celery.task` passes an explicit `name=`; never rename it or derive it from `__name__`. New tasks use `project.<module path>.<func>` of their real module; the frozen set lives in `tests/integration/infrastructure/test_celery_app.py`.
- Deferred SQLAlchemy columns may require explicit `undefer()` in query options.
- Avoid editing generated files or relying on behavior that codegen overwrites.
- Query handlers must return materialized read models; the read session is closed when the bus returns.
- Commands are defined in [project/application/commands/](../project/application/commands/), not in a domain commands package.

## Canonical References

- Development guide: [doc/development.md](../doc/development.md)
- Deployment guide: [doc/deployment.md](../doc/deployment.md)
- Project overview: [README.md](../README.md)
