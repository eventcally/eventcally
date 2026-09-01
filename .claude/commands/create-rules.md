---
description: Create global rules (CLAUDE.md) from codebase analysis
---

# Create Global Rules

Generate a CLAUDE.md file by analyzing this Python/Flask codebase and extracting patterns.

---

## Objective

Create project-specific global rules that give Claude context about:

- What this project is
- Technologies used
- How the code is organized
- Patterns and conventions to follow
- How to run, test, and validate

> **Note:** This repo already ships an `AGENTS.md` and, more importantly,
> `.github/copilot-instructions.md` (the primary agent instructions) with
> mission-critical context, run commands, architecture boundaries, and pitfalls.
> Read both first and treat them as the source of truth — CLAUDE.md should reuse
> and complement them, not contradict them.

---

## Phase 1: DISCOVER

### Confirm Project Type

This is **EventCally**, a **Flask event-calendar platform** (Flask + SQLAlchemy +
Celery + PostgreSQL/PostGIS + Redis) built with **Domain-Driven Design**. Verify
nothing has diverged from that, then note the shape:

| Type | Indicators |
| ------ | ------------ |
| Web app + REST API | Flask app (`bootstrap.py` → `create_app()`), `project/views/`, `project/api/` |
| DDD command/event core | `project/application/` (commands, handlers, message bus) over `project/domain/` |
| Async workers | Celery tasks (`project/celery_tasks.py`), celery beat, Flower |
| Geo data | PostGIS + GeoAlchemy2 for locations/places |

### Analyze Configuration

Look at root configuration files:

```text
requirements.txt        → dependencies (pinned)
.flake8                 → flake8 rules (ignores E501/E203/E711; per-file ignores)
.isort.cfg              → import sort (black profile; skips *_generated.py)
pytest.ini              → pytest config
.pre-commit-config.yaml → pre-commit hooks (isort, black, flake8, import checks)
.importlinter           → DDD layer contract (infrastructure → application → domain)
.flaskenv / .env        → Flask + runtime env vars (FLASK_APP=bootstrap.py)
Dockerfile / docker-compose*.yml → container + local dev services
bootstrap.py / main.py  → entrypoints (both call create_app())
migrations/             → Alembic (Flask-Migrate) DB migrations
codegen/                → YAML-driven model/repo code generation
```

### Map Directory Structure

Explore the codebase to understand organization:

- `project/` — application package (Flask wiring, views, api, DDD layers, tasks)
- `project/domain/` — models, abstract interfaces, business logic (no app/infra imports)
- `project/application/` — commands, command/event handlers, message bus, read models
- `project/infrastructure/` — concrete adapters (SQLAlchemy repos, Celery dispatchers, services)
- `project/api/` — REST API resources and marshmallow schemas
- `project/views/`, `project/forms/`, `project/templates/` — server-rendered UI
- `codegen/` — `generate.py` + YAML schemas under `codegen/config/`
- `tests/` — pytest suites mirroring source structure; `conftest.py`, `base_test.py`, `seeder.py`
- `cypress/` — end-to-end tests
- `doc/`, `deployment/`, `.scripts/` — docs and ops/lint helpers

---

## Phase 2: ANALYZE

### Extract Tech Stack

From `requirements.txt` and configs, identify:

- **Language/Runtime**: Python (3.12 in CI, 3.11 for pre-commit), virtualenv in `venv/`
- **Web framework**: Flask 3 (+ Flask-SQLAlchemy, Flask-Migrate, Flask-Security-Too, Flask-Admin, Flask-RESTful, flask-apispec)
- **Architecture**: DDD with a `dependency-injector` DI container; import layering enforced by `import-linter`
- **Task queue**: Celery 5 (+ Redis broker, celery beat, Flower)
- **Database**: PostgreSQL + PostGIS via psycopg2 + SQLAlchemy 2 ORM + GeoAlchemy2; Alembic migrations
- **Rate limiting**: Flask-Limiter (dedicated `LIMITER_REDIS_URL`)
- **Server**: gunicorn
- **Testing**: pytest (+ pytest-split, pytest-cov, pytest-mock); Cypress for e2e
- **Lint/format**: black, isort, flake8, import-linter, pre-commit
- **Other**: marshmallow (serialization), pydantic (commands), Babel (i18n), icalendar/recurring-ical-events, googlemaps, Authlib/Flask-Dance (OAuth)

### Identify Patterns

Study existing code for:

- **DDD layering**: `domain` ← `application` ← `infrastructure`; never import "up" a layer (checked by `lint-imports` and `.scripts/module_import_whitelist.py`)
- **Commands/events**: Pydantic `Command`/`CommandWithResult[T]` in `project/application/commands/`, handlers in `command_handlers/`, wired through the message bus and DI container (`project/container.py`)
- **Generated code**: `*_generated.py` from `codegen/config/` YAML — never edit by hand; put custom logic in the handwritten sibling (e.g. `event.py` extends `event_generated.py`)
- **Data access**: SQLAlchemy ORM via repositories; watch for deferred columns needing `undefer()`
- **Tests**: fixtures/base classes in `tests/conftest.py` + `tests/base_test.py`; assert through message bus / repositories, not around the architecture
- **Errors, naming, structure**: snake_case, thin views delegating into application/domain

### Find Key Files

- App bootstrap/wiring: `project/__init__.py`, `bootstrap.py`
- DI container: `project/container.py`
- Message bus: `project/application/message_bus.py`
- Commands / handlers: `project/application/commands/`, `project/application/command_handlers/`
- Domain models: `project/domain/models/`
- API wiring: `project/api/__init__.py`
- Tasks/schedules: `project/celery_tasks.py`, `project/base_tasks.py`
- Codegen: `codegen/generate.py`, `codegen/config/`
- Test fixtures: `tests/conftest.py`, `tests/base_test.py`, `tests/seeder.py`
- CI: `.github/workflows/lint.yml`, `.github/workflows/test.yml`, `.github/workflows/cypress.yml`
- Agent docs: `AGENTS.md`, `.github/copilot-instructions.md`, `doc/development.md`, `doc/deployment.md`

---

## Phase 3: GENERATE

### Create CLAUDE.md

There is no template in `.claude/` — write CLAUDE.md from scratch, drawing on
`AGENTS.md` and `.github/copilot-instructions.md`.

**Output path**: `CLAUDE.md` (project root)

> **Exception to the date-prefix rule:** generated markdown normally gets a `YYYY-MM-DD-`
> prefix (see `/plan`, `/implement`), but `CLAUDE.md` is a fixed, tool-loaded filename —
> write it as `CLAUDE.md`, never `2026-09-01-CLAUDE.md`.

**Adapt to the project:**

- Remove sections that don't apply
- Keep it concise — focus on what's useful
- Don't restate `AGENTS.md` / `copilot-instructions.md` verbatim; link to them and add only what's missing

**Key sections to include:**

1. **Project Overview** — EventCally: Flask + SQLAlchemy + Celery event-calendar platform built with DDD
2. **Tech Stack** — key technologies (see above)
3. **Commands** — how to install, run, test, lint
4. **Structure** — how `project/` is organized and the domain → application → infrastructure flow
5. **Patterns** — DDD layering, commands/handlers + message bus, codegen rules, ORM repositories
6. **Key Files** — the reference files listed above

**Optional sections (add if relevant):**

- Architecture & data flow (command → handler → repository, event dispatch, Celery scheduling)
- Database patterns & migrations (Alembic via Flask-Migrate, PostGIS diff caveats)
- Pitfalls (import-layer violations, never editing `*_generated.py`, registering new Celery tasks, deferred columns needing `undefer()`, required env vars)

---

## Phase 4: OUTPUT

```markdown
## Global Rules Created

**File**: `CLAUDE.md`

### Project Type

Flask event-calendar platform (Flask + SQLAlchemy + Celery + PostGIS + Redis), DDD architecture

### Tech Stack Summary

{Key technologies detected}

### Structure

{Brief structure overview}

### Next Steps

1. Review the generated `CLAUDE.md`
2. Reconcile with `AGENTS.md` and `.github/copilot-instructions.md` (no contradictions)
3. Add any project-specific notes
4. Remove any sections that don't apply
```

---

## Reference Commands

```bash
# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run (needs DATABASE_URL, SECRET_KEY, SERVER_NAME, REDIS_URL, LIMITER_REDIS_URL, GOOGLE_MAPS_API_KEY, mail settings)
flask db upgrade
flask run --host 0.0.0.0
# or full stack via Docker (PostGIS, Redis, Mailhog, Flask, Celery worker/beat, Flower):
docker-compose up --build

# Test (application/ and domain/ tests need no services; the rest need PostGIS + Redis)
docker-compose -f docker-compose.test.services.yml up -d
pytest                             # all tests
pytest --cov=project --cov-report=html   # with coverage
pytest tests/views/test_event.py::TestEventView::test_create -v   # single test

# End-to-end
npm install && npx cypress run

# Regenerate model/repo code after editing codegen/config/ YAML
python codegen/generate.py

# Lint / format (order matters — run before commit)
isort . && black . && flake8 && lint-imports && \
  python .scripts/module_import_whitelist.py project/domain project/application
# or simply:
pre-commit run --all-files
```

---

## Tips

- Keep CLAUDE.md focused and scannable
- Link to `AGENTS.md`, `.github/copilot-instructions.md`, and `doc/` instead of duplicating them
- Focus on patterns and conventions, not exhaustive documentation
- Respect the DDD import layering (`domain` ← `application` ← `infrastructure`) — never cross it
- Never edit `*_generated.py`; change the YAML in `codegen/config/` and regenerate
- Register new Celery tasks in `project/celery_tasks.py`
- Update it as the project evolves
