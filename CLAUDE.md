# CLAUDE.md

Guidance for Claude when working in this repository.

> This is the primary agent instruction file. [`AGENTS.md`](AGENTS.md) supplements it with
> operational details (lint order, import whitelists, test and e2e setup, frontend workflow).
> Scaffolding guides live in `.claude/commands/` (`/add-ddd-command`, `/add-ddd-event`,
> `/add-ddd-query`).

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
docker-compose up --build                      # full stack: PostGIS, Redis, Mailpit, Flask, Celery, Flower

# Test — dockerized, no host Postgres/Redis/venv needed (`pytest tests/unit` needs no services)
./runtests.sh                                  # full parallel suite + coverage, in Docker
pytest --cov-report=html --cov=project         # coverage against your own services
# Subset/single test: pass paths after `--`. Needs a group, which creates that group's
# database and exports TEST_DATABASE_URL — plain `run --rm pytest pytest <path>` fails
# with `could not translate host name "myserver"`.
./runtests.sh --splits 1 --group 1 -- tests/integration/presentation/web/views/test_event.py::test_create_allday -v --no-cov
# Slices (unit, infra, web, api, bff, misc; map in .scripts/test_slices.py): tests/unit + the slice's tests
./runtests.sh --slice web                      # one slice (comma-separate several); prints its own coverage
./runtests.sh --changed                        # slices touched vs origin/main (coverage ownership, not regression safety)
python .scripts/test_slices.py check           # per-slice coverage table from the combined .coverage
./runtests.sh --store-durations                # refresh .test_durations (full suite only)
# CI runs `.scripts/run_tests.sh --shard J --shards M --splits N --no-report` (global groups (J-1)*N+1..J*N,
# database per global group, Redis index per local group; credentials/ports via TEST_DB_CREDENTIALS,
# TEST_REDIS_CREDENTIALS (empty = no auth), TEST_REDIS_PORT, TEST_LIMITER_REDIS_PORT). CI-speed
# durations: run the Tests workflow via workflow_dispatch with `store_durations`, commit the
# `test-durations` artifact as .test_durations.
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
  - `bff/` — JSON for the Vue 3 frontends under `/bff` (blueprint, session + CSRF auth, `bff_route` registry → OpenAPI 3.1 via `python -m project.presentation.bff.openapi`); reads through `query_bus`; imports neither `web` nor `api`; anonymous only under `bff/public` (`/bff/public`: CSRF + rate-limited writes; Vite entry `public`, pages `/event/<id>/report`, `/organizers/<id>`, `/organizations[/<id>]`, `/eventdates`; the place lookups under `/bff/public/places` are rate limited because they call Google); `bff/manage` (`/bff/manage`) is session only, each route authorizes its own use case (Vite entry `manage`, `/planning`, the event list `/manage/admin_unit/<id>/events` (endpoint `manage_admin_unit.events`, legacy query names kept), the organization create form `/manage/organization/create` (endpoint `manage.organization_create`; the Flask shell route gates it, `presentation/shared/organization_create.py` is the gate shared with the BFF; both organization forms share `OrganizationFormFields.vue` and `GET /bff/manage/organizations/name-availability`), the organization settings form `/manage/admin_unit/<id>/update` (endpoint `manage_admin_unit.update`; the first shared `ImageField`/`ImageCropper`/`LocationFields` building blocks, Google place address under `/bff/manage/places/<id>/address`) the organizer create/update form `/manage/admin_unit/<id>/event_organizer/create` and `.../event_organizer/<oid>/update` (endpoints `manage_admin_unit.event_organizer_create`/`_update` stay modular shell views; `bff/manage/event_organizers.py`; the Google lookup sits inside `LocationFields` and fills only the address) the place create/update form `/manage/admin_unit/<id>/event_place/create` and `.../event_place/<pid>/update` (endpoints `manage_admin_unit.event_place_create`/`event_place_update` stay modular shell views; the Google lookup is the shared `PlaceLookup`, `LocationFields` takes `lookup`/`required`; `/bff/manage/organizations/<id>/event-places`) and the custom widget configurator; the organization export page `/manage/admin_unit/<id>/export` (endpoint `main.manage_admin_unit_export`; `StartOrganizationExportCommand` + `GetOrganizationExport[JobStatus]Query` through the export dispatcher/reader ports, job ids `org-export-<id>-<uuid>` so a status poll only answers for the organization's own jobs; the download stays the Flask route `main.manage_admin_unit_export_dump_files`); the incoming reference / verification request review pages `/manage/admin_unit/<id>/incoming_event_reference_request/<rid>/review` and `.../incoming_organization_verification_request/<vid>/review` (endpoints `manage_admin_unit.incoming_event_reference_request_review` / `incoming_organization_verification_request_review` stay modular shell views that keep the already-verified flash + redirect; `bff/manage/request_reviews.py` serves one GET per page and verify/approve/reject POSTs that map to the existing commands, 404 when the request belongs to another organization, flash + `redirect_url`; shared `LinkifiedText`, `event_rating_choices` lives in `presentation/shared/event_rating.py`); the outgoing relation forms `/manage/admin_unit/<id>/outgoing_organization_relation/create` and `.../<rid>/update` (endpoints `manage_admin_unit.outgoing_organization_relation_create`/`_update` stay modular shell views; `bff/manage/outgoing_relations.py`: create/update forms, the organization lookup, POST/PUT; the `verify` switch only with `can_verify_other`, decided server side; `?target=<id>&verify=1` prefills the create form) and the outgoing reference request form `/manage/admin_unit/<id>/outgoing_event_reference_request/create_for_event/<event_id>` (endpoint `manage_admin_unit.outgoing_event_reference_request_create_for_event` keeps the `can_request_event_reference` guard; `bff/manage/outgoing_reference_requests.py`; the success text lives in `presentation/shared/reference_request.py`; a duplicate request answers 400 `DuplicateError`, shown as an alert; both pages use `AppTypeahead` instead of select2); the event create/update form `/manage/admin_unit/<id>/event/create` (`?template_id=` copies an event, also of another organization: its place, organizer, co-organizers, internal tags and rating stay empty) and `.../event/<eid>/update` (endpoints `manage_admin_unit.event_create`/`event_update` stay modular shell views; `bff/manage/event_forms.py`: create-form/form GETs, POST/PUT, the recurrence preview `POST .../events/occurrences` and the custom category lookup; dates are naive Berlin wall-clock `YYYY-MM-DDTHH:MM`; "+ New" opens `EventPlaceCreateModal`/`EventOrganizerCreateModal`, which post to the place/organizer create routes with `inline: true` (no flash) and reuse `EventPlaceFormFields`/`EventOrganizerFormFields`; `RecurrenceRuleModal` + `recurrenceRule.ts` edit only the RRULE subset the legacy widget writes and keep any other rule unchanged; the previous WTForms form lives on under `.../legacy/event/create` and `.../legacy/event/<eid>/update` (endpoints `event_legacy_create`/`_update`, `web/views/manage_admin_unit/event_legacy/`), linked from the top of the Vue form by `LegacyFormLink`); event reference writes of the `/eventdates` page); the `widget` entry is the embedded widget (`/custom_widget/<type>`, reads through `bff/public/widget`)
  - `web/` — server-rendered site: `views/`, `modular/` (the shared modular CRUD view framework), `forms/`, `templates/`, `static/`, `jinja_filters.py`
  - `api/` — REST resources + marshmallow schemas (flat; the version lives in the `/api/v1` URL prefix). `/api/v1` authenticates only with OAuth tokens or API keys (anonymous reads when `API_READ_ANONYM`); it ignores the session cookie. Browser clients use `/bff`. Organization-owned resources use `/organizations/<id>/{incoming,outgoing}-<things>[/<thing_id>]` like the web routes (decorator `item_arg` answers 404 for another organization's or the other side's item); the id-only routes are deprecated (declared with `add_api_resource(..., deprecated="<replacement>")`, marked in Swagger) and hidden by the `ApiDeprecatedEndpointsDisabled` flag.
  - `cli/` — Flask CLI commands (outside the read-path contract: `cli/test.py` is a dev/e2e fixture CLI)
  - `shared/` — cross-**channel** helpers (`access`, `permissions`, `oauth2_extensions`, `query_args`, `query_results`, `current_admin_unit`, `scopes`, `rate_limit`, `urls`)
- `project/templates/email/` — e-mail templates; they stay outside `presentation/web` because infrastructure renders them (also from Celery). Flask loads both template roots through a `ChoiceLoader`
- `frontend/` — Vite + TypeScript + Vue 3 + bootstrap-vue-next (one entry per area, build → `project/presentation/web/static/dist/`, resolved by the Jinja global `vite_entry`); the admin SPA is served at `/admin` (Flask-Admin stays at `/admin/flask-admin/`). See § Frontend below
- `.scripts/codegen/` — `generate.py` + YAML schemas in `.scripts/codegen/config/`
- `tests/` — `unit/` (no services: domain, application, pure helpers) and `integration/` (PostGIS + Redis; holds `conftest.py`, `base_test.py`, `seeder.py`). **Tests mirror the source tree**: the tests of `project/presentation/web/views/event.py` live in `tests/integration/presentation/web/views/test_event.py`
- `e2e/`, `doc/`, `deployment/`, `.scripts/`

**Flow:** reads: view / API → `query_bus` → query handler → read repository (read model out); writes: view / API → `message_bus` → command handler → repository (domain via infrastructure); events dispatch through the message bus, some onto Celery.

## Patterns

- **DDD layering (strict):** `domain` ← `application` ← `infrastructure` ← `presentation`. Never import "up" a layer. Enforced by `.importlinter` (`lint-imports`) and `.scripts/module_import_whitelist.py`; allowed imports live in `project/domain/allowed_imports.cfg` and `project/application/allowed_imports.cfg`.
- **Shared packages:** `project.shared` is shared across **layers** and is a leaf (it may import only `project.domain`). `project.presentation.shared` is shared across **channels** (web, API). Web, API and BFF never import each other (contracts `web-does-not-import-api`, `api-does-not-import-web`, `bff-is-its-own-channel`, `web-and-api-do-not-import-bff`, `presentation-shared-is-channel-neutral`). Put a helper both channels need in `presentation/shared/`.
- **Tests mirror the source tree:** a module's tests live at the mirrored path (`tests/{unit,integration}/<path below project/>/test_<module>.py`). Fixtures stay in `tests/integration/`.
- **Commands/events:** pydantic `Command` / `CommandWithResult[T]` in `project/application/commands/`, handlers in `command_handlers/`, registered in the DI container (`project/container.py`) and driven through `message_bus.py`. The `actor` field is auto-added. Scaffolds: `/add-ddd-command`, `/add-ddd-event` (`.claude/commands/`).
- **Read side (queries):** every read in views (incl. `web/modular`)/API goes through pydantic `Query[T]` objects in `project/application/queries/`, dispatched via `QueryBus` (`Application.cqrs.query_bus`; `BaseResource.query_bus`, `BaseView.query_bus`). Handlers in `query_handlers/` get read repos by constructor injection and return hand-written, use-case shaped read models (`read_models/`, `Page[T]` for lists). Query read repos use `infrastructure.read_session` (read-only, released after each top-level query); event-handler read repos stay on `session_factory`. Modular list and object views implement `create_list_query()` / `create_get_query()` (there is no ORM list path any more). Search criteria are pydantic models (`EventSearchCriteria`); visibility rules live in handlers/services (`EventVisibilityService`). Access decisions use the same permission policy (`project/presentation/shared/access.py` is a thin wrapper; API decorators take a `ResourceKind`). Scaffold: `/add-ddd-query` (`.claude/commands/add-ddd-query.md`); reference implementation: event organizers (`ListEventOrganizersQuery`, `SqlAlchemyEventOrganizerReadRepository`). Query handlers for private data authorize the actor via `ActorAuthorizationService` (same rule as commands, `actor_permission_policy`); reference: organization invitations (`ListOrganizationInvitationsQuery`).
- **Import ratchet:** the `delivery-reads-through-queries` contract in `.importlinter` forbids `project.presentation.web` / `project.presentation.api` / `project.presentation.shared` → `project.infrastructure.models` (`presentation.cli` is outside), with an `ignore_imports` list that only holds the permanent exemption `presentation.web.views.flask_admin` (Flask-Admin stays ORM; Flask-Security `current_user` and Authlib stay too). Regenerate with `python .scripts/models_import_ignores.py --write` after removing imports; never add entries by hand. Progress: `python .scripts/read_path_report.py`.
- **Generated code:** `*_generated.py` is generated from `.scripts/codegen/config/` YAML — **never edit it**. Put custom logic in the handwritten sibling (e.g. `event.py` extends `event_generated.py`). isort/flake8 already skip these files.
- **Data access:** SQLAlchemy ORM through repositories; deferred columns may need explicit `undefer()`.
- **Test slices:** each slice owns part of `project/` (`.scripts/test_slices.py`) and, with `tests/unit`, must cover it at 100% on its own (checked from `--cov-context=test` data). A slice in `ENFORCED` must stay at 100%; add yours when it gets there. CI always runs the full suite and the global 100% gate.
- **Tests:** reuse fixtures from `tests/integration/conftest.py` (`app`, `db`, `client`, `seeder`, `utils`, `container`, `message_bus`) and base classes in `tests/integration/base_test.py`; assert through the message bus / repositories, not around the architecture. **The `app` fixture is shared per test process** (built once while collecting; `create_app()` runs again only after a test called it itself): a test may change `app.config` and container overrides (both restored after each test) but must not register routes, hooks or extensions on it. Call `create_app()` for that. Module-level lines of `presentation/api` and `presentation/web` are imported while collecting so their coverage does not depend on which test runs first; template-compile-time code (e.g. folded Jinja filters) needs a direct unit test.

## Frontend (Vue 3 + BFF)

- `frontend/` is one Vite + TypeScript + Vue 3 + bootstrap-vue-next project with one entry per area (`src/apps/<area>/main.ts`; areas: `admin`, `public`, `manage`, `widget`, registered in `vite.config.ts` and `project/presentation/web/vite.py:ENTRIES`). The build lands in `project/presentation/web/static/dist/` (gitignored); the Jinja global `vite_entry(name)` renders its tags (or the dev server's when `VITE_DEV_SERVER_URL` is set).
- Pages are shells: `layout_vue3.html` extends the Bootstrap 5 frame `layout_bs5.html` and hands the SPA its boot JSON. The SPA must not import Bootstrap CSS (the frame provides it). The old frames `layout.html` (BS4) / `layout_vue.html` (Vue 2) stay untouched; the navbar links of both frames come from `get_main_menu()`.
- `widget` is the embedded custom widget (`/custom_widget/<search|calendar>`, iframe on customer sites): it has its own minimal shell `custom_widget/widget.html`, reads through `/bff/public/widget/...` and keeps the iframeResizer message protocol and the stored settings keys wire-compatible (`/js/wlcw/<id>`, `static/widget-loader.js`).
- BFF routes are declared with `bff_route(...)` (`project/presentation/bff/routing.py`) with pydantic query/body/response models. After changing a BFF model regenerate `frontend/openapi.json` + `frontend/src/api/schema.d.ts` and commit both (pytest and CI check the drift).
- The admin SPA owns `/admin/*` (catch-all shell `admin.shell`); unknown paths render the SPA's not-found page. Server-rendered pages the SPA links to live in `frontend/src/shared/legacy.ts`.
- Tag inputs (`BFormTags`, replacing select2 tags): placeholder is the field's own noun ("Add postal code" → "Postleitzahl hinzufügen"), always shown while the input is empty (the old fields had none, but an empty box is unclear); hide the add button (`.b-form-tags-button`, Enter/comma/space add tags and the button overflows the field), pin the field to single-line input height, make the tag close button white, and translate the duplicate/invalid/remove texts (`duplicate-tag-text`, `invalid-tag-text`, `tag-remove-label`, `tag-removed-label`). Reference: `OrganizationSettingsPage.vue`.
- Translations: the Babel `.po` files stay the single source. Use literal `t("English msgid")` calls in `.vue`/`.ts` (dynamic keys are not extracted); `npm run i18n` turns the `.po` files into `src/locales/*.json`.
- Workflow commands (dev server, typecheck, tests, build): see `AGENTS.md` § Frontend.

## Pitfalls

- After changing BFF pydantic models regenerate `frontend/openapi.json` and `frontend/src/api/schema.d.ts` (`python -m project.presentation.bff.openapi > frontend/openapi.json && npm run gen:api --prefix frontend`); never hand-edit `schema.d.ts`. The SPA must not import Bootstrap CSS (the Jinja frame provides it).
- New Celery tasks must be imported/registered in `project/presentation/tasks/celery_tasks.py`.
- Dependabot (`.github/dependabot.yml`) bumps image tags, actions, `uv.lock` and the npm locks, but not the setup-node `node-version`, setup-uv `version`, the uv `COPY --from` tag or `.pre-commit-config.yaml`. When a Node image PR lands, bump `node-version` in `frontend.yml` / `playwright.yml` in the same PR; a `@playwright/test` PR also bumps the `Dockerfile.e2e` tag. Version updates are minor/patch only (GitHub Actions also get majors, grouped): major updates, black, isort, flake8, import-linter, PostGIS, the Python minor and the Playwright image are ignored and bumped by hand (black/isort/flake8/import-linter are pinned in `pyproject.toml`/`uv.lock`, which `lint.yml` runs, in lockstep with `.pre-commit-config.yaml`; bump both together). Security updates ignore the `update-types` (major) rules but not name-level ignores: black, isort, flake8, import-linter, PostGIS and the Playwright image get their security fixes by hand when an alert appears, so check them before merging.
- `main` is protected by a repository ruleset (no force push/deletion, PR required, required checks `lint`, `main`, `unit-tests`, `integration-tests (1)`–`(4)`, `coverage`, `frontend`, `playwright (1)`–`(3)`, `CodeQL`, strict: the branch must be up to date). Renaming a workflow job or matrix changes the check name: update the ruleset in the same PR or merges block. Workflows set their own `permissions:` (the repo default token is read-only).
- Commands live in `project/application/commands/`, not in a domain commands package.
- Celery task names are a wire contract: every `@celery.task` passes an explicit `name=`; never rename it or derive it from `__name__`. New tasks use `project.<module path>.<func>` of their real module; the frozen set lives in `tests/integration/infrastructure/test_celery_app.py`.
- E-mail templates stay in `project/templates/email/` and import the web macros (`_macros.html`); Flask resolves both roots (`presentation/web/templates`, then `project/templates`) via a `ChoiceLoader` set in `create_app`. `babel.cfg` lists both.
- `project/translations/` stays in `project/` (Flask-Babel resolves it from `app.root_path`).
- `presentation/cli` is outside the read-path contract (it writes fixtures through the ORM via `infrastructure/seed_helpers.py`).
- Query handlers must return materialized read models; the read session is closed when the bus returns, so lazy loads fail. The read session only sees committed data.
- PostGIS migration diffs from `flask db migrate` sometimes need manual correction — always review before `upgrade`.
- flake8 ignores E501/E203/E711 (Black owns formatting); don't fight isort skipping `*_generated.py`.
- Never hand-edit `uv.lock`: use `uv add <pkg>` / `uv add --dev <pkg>` / `uv lock --upgrade-package <pkg>`. CI and Docker run `uv sync --locked`, so commit `uv.lock` together with `pyproject.toml`.
- The Swagger 2.0 document (`/swagger/`) is kept stable across apispec versions by `StableMarshmallowPlugin` (`presentation/api/apispec_plugin.py`); `test_openapi_snapshot` guards it. Regenerate the snapshot only for intended API changes (`UPDATE_READ_PARITY=1`).
- Required env vars for running: `DATABASE_URL`, `SECRET_KEY`, `SERVER_NAME`, `REDIS_URL`, `LIMITER_REDIS_URL`, `GOOGLE_MAPS_API_KEY`, mail settings (see `doc/development.md`).

## Key Files

- Bootstrap/wiring: `project/factory.py`, `project/config.py`, `bootstrap.py` (`FLASK_APP` set in `.flaskenv`)
- DI container: `project/container.py`
- Message bus: `project/application/message_bus.py`; query bus: `project/application/query_bus.py`
- Commands / handlers: `project/application/commands/`, `project/application/command_handlers/`
- API wiring: `project/presentation/api/__init__.py`
- Cross-layer / cross-channel helpers: `project/shared/`, `project/presentation/shared/`
- Tasks: `project/presentation/tasks/celery_tasks.py`, `project/infrastructure/celery_base_tasks.py`
- Codegen: `.scripts/codegen/generate.py`, `.scripts/codegen/config/`
- Tests: `tests/integration/conftest.py`, `tests/integration/base_test.py`, `tests/integration/seeder.py`
- CI: `.github/workflows/{lint,test,playwright}.yml`
- Docs: `doc/development.md` (full environment setup), `doc/deployment.md`, `README.md`
