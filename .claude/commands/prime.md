---
description: Prime agent with codebase understanding
argument-hint: [github-issues]
---

# Prime: Load Project Context

**Input**: $ARGUMENTS

## Objective

Build comprehensive understanding of this Flask + SQLAlchemy + Celery + PostGIS codebase
(EventCally, a Domain-Driven-Design event-calendar platform) by analyzing structure and
key files.

## Process

### Step 0: Load External Context (if provided)

The argument is an optional GitHub issue reference or comma-separated list (e.g. `11` or
`#11,#12`, or a full issue URL).

If issues are provided, for each one run:

```bash
gh issue view <number> --json number,title,body,labels,state,comments
```

Use the issue title, body, labels, and comments to understand what work is expected. If the
repo has no GitHub remote configured, note that and continue with codebase analysis only.

### Step 1: Analyze the Codebase

1. Read `CLAUDE.md`, `AGENTS.md`, and `.github/copilot-instructions.md` for conventions,
   architecture guardrails, and pitfalls
2. Study the app wiring: `project/__init__.py` (`create_app`), `project/container.py` (DI),
   `bootstrap.py` (entrypoint)
3. Study the DDD layers:
   - `project/domain/` — models, abstract interfaces, business logic
   - `project/application/` — commands, command/event handlers, `message_bus.py`
   - `project/infrastructure/` — SQLAlchemy repos, Celery dispatchers, external services
4. Study the delivery layers: `project/api/` (REST + marshmallow schemas), `project/views/`
5. Note the async + codegen entry points: `project/celery_tasks.py`, `codegen/generate.py`
   (+ YAML in `codegen/config/`)
6. Check recent commits with `git log --oneline -5`

## Output

Produce a scannable summary of what you learned:

- **Project Purpose**: One sentence
- **Tech Stack**
  - Web: Flask + extensions (SQLAlchemy, Migrate, Security-Too, Admin, RESTful, apispec)
  - Architecture: DDD with a `dependency-injector` container; layering enforced by `import-linter`
  - Data: PostgreSQL + PostGIS via SQLAlchemy 2 ORM + GeoAlchemy2; Alembic migrations
  - Async: Celery workers + beat scheduler (Redis broker), Flower
- **Data Model**: Core entities (from `project/domain/models/` and `codegen/config/models/`)
- **Key Patterns**: DDD layering (`domain` ← `application` ← `infrastructure`); commands →
  handlers → message bus; repositories over the ORM; `*_generated.py` from codegen
- **Current State**: Recent commits, current branch, any issue context loaded

Use bullet points. Keep it concise.
