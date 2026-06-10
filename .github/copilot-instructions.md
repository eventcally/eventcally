# EventCally Agent Instructions

EventCally is a Flask + SQLAlchemy event calendar platform using Domain-Driven Design patterns.

## Agent Quickstart

- Install dependencies: `pip install -r requirements.txt`
- Run app locally: `./runlocal.sh`
- Run unit tests: `pytest`
- Run coverage tests: `pytest --cov-report=html --cov=project`
- Run parallel test script: `./runpytest.sh`
- Run e2e tests: `npm install && ./runcypress.sh`
- Run lint/format checks before commit: `pre-commit run --all-files`

For full environment setup, use [doc/development.md](../doc/development.md).

## Architecture Guardrails

Respect strict DDD layering:

- `project/domain/`: core business logic and abstract interfaces
- `project/application/`: commands, handlers, message bus orchestration
- `project/infrastructure/`: concrete adapters (SQLAlchemy, Celery, external services)

The layering rule is enforced by [.importlinter](../.importlinter). Avoid introducing imports that violate these boundaries.

Primary integration points:

- DI container: [project/container.py](../project/container.py)
- Message bus: [project/application/message_bus.py](../project/application/message_bus.py)
- API wiring: [project/api/__init__.py](../project/api/__init__.py)

## Generated Code Rules

- Never edit `*_generated.py` files directly.
- Update YAML model schemas under [codegen/config/](../codegen/config/) and regenerate with `python codegen/generate.py`.
- Put custom model logic in handwritten extensions (for example `event.py` extending `event_generated.py`).

## Database, Migrations, and PostGIS

- Use Postgres with PostGIS extension in both dev and test databases.
- After model changes: `flask db migrate`, then review migration, then `flask db upgrade`.
- Be careful with PostGIS-related migration diffs; they sometimes need manual correction.

## Testing Conventions

- Prefer existing fixtures and app context setup from [tests/conftest.py](../tests/conftest.py).
- Keep tests aligned with source structure (application/api/infrastructure/domain).
- For command/event flows, assert behavior through the message bus and repository interfaces instead of bypassing architecture.

## Common Pitfalls

- New Celery tasks must be imported/registered in [project/celery_tasks.py](../project/celery_tasks.py).
- Deferred SQLAlchemy columns may require explicit `undefer()` in query options.
- Avoid editing generated files or relying on behavior that codegen overwrites.
- Commands are defined in [project/application/commands/](../project/application/commands/), not in a domain commands package.

## Canonical References

- Development guide: [doc/development.md](../doc/development.md)
- Deployment guide: [doc/deployment.md](../doc/deployment.md)
- Project overview: [README.md](../README.md)
