# EventCally - Workspace Instructions

Open event calendar platform built with Flask, SQLAlchemy, and Domain-Driven Design.

## Architecture

EventCally follows **Domain-Driven Design** with clear layer separation:

- `project/domain/` - Domain logic, abstract repositories, commands, events
- `project/infrastructure/` - Concrete implementations (SQLAlchemy repositories, Celery dispatchers)
- `project/service_layer/` - Command/event handlers, message bus orchestration
- `project/models/` - SQLAlchemy models (many auto-generated)
- `project/repos/` - Repository implementations
- `project/api/` - REST API endpoints
- `project/views/` - Web UI views

Key architectural patterns:
- **Command Pattern**: Actions are modeled as command objects dispatched through message bus
- **Event-Driven**: Domain events trigger side effects via event handlers
- **Repository Pattern**: Data access abstracted via interfaces in `domain/`, implemented in `infrastructure/`
- **Unit of Work**: Transaction management via `SqlAlchemyUnitOfWork`
- **Dependency Injection**: Centralized container in [`project/container.py`](../project/container.py)

## Code Generation

**CRITICAL**: Files ending in `*_generated.py` are auto-generated from YAML schemas in [`codegen/config/`](../codegen/config/).

- **Never manually edit** `*_generated.py` files
- To modify models, edit the YAML schema and regenerate: `python codegen/generate.py`
- Generated files are mixins extended by hand-written models
- Linting rules ignore generated files (F401, E303, W391)

Example: `project/models/event_generated.py` (generated) → extended by `project/models/event.py` (handwritten)

## Code Style

Enforced via pre-commit hooks:

- **black**: Auto-formatting (profile: black)
- **isort**: Import sorting (multi_line_output=3, profile=black)
- **flake8**: Linting with extensions (E501, E203, E711 ignored)

Config files: [`.flake8`](../.flake8), [`.isort.cfg`](../.isort.cfg), [`.pre-commit-config.yaml`](../.pre-commit-config.yaml)

**Run before committing**: `pre-commit run --all-files`

## Build and Test

### Local Development

```bash
# Install dependencies
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Database setup
psql -c 'create database eventcally;' -U postgres
psql -c 'create extension postgis;' -d eventcally -U postgres
flask db upgrade

# Run locally
./runlocal.sh
```

### Testing

```bash
# Create test database (one-time)
psql -c 'create database eventcally_tests;' -U postgres
psql -c 'create extension postgis;' -d eventcally_tests -U postgres

# Run unit tests
pytest

# With coverage
pytest --cov-report=html --cov=project

# E2E tests
npm install
./runcypress.sh
```

See [doc/development.md](../doc/development.md) for full setup.

## Dependency Injection

Services and repositories injected via [`project/container.py`](../project/container.py):

- Container organized into: `Infrastructure`, `Context`, `Repos`, `Services`, `MessageBus`
- Access via `current_app.container.repos.event_repo()` or inject into handlers
- Repositories follow Abstract (domain) → Concrete (infrastructure) pattern

## Database Migrations

```bash
# Create migration after model changes
flask db migrate

# Apply migrations
flask db upgrade
```

**Always review** generated migrations before committing.

## Internationalization

Babel-based i18n workflow (supported: `en`, `de`):

```bash
# Extract translatable strings
.scripts/translations/extract.sh

# Add new locale
.scripts/translations/add_locale.sh <locale>

# Compile translations
.scripts/translations/compile.sh
```

## Celery Tasks

Asynchronous tasks via Celery:

- Task definitions: [`project/celery_tasks.py`](project/celery_tasks.py)
- Command dispatching: `CeleryCommandDispatcher` for async command execution
- Run worker: `celery -A project.celery worker --loglevel=debug`

## Common Patterns

### Adding a New Feature (DDD Style)

1. **Define command** in `project/domain/commands/` (inherit from `Command` or `CommandWithResult`)
2. **Create handler** in `project/service_layer/command_handlers/`
3. **Register handler** in message bus (`project/service_layer/message_bus.py`)
4. **Add to container** if new repository/service needed (`project/container.py`)
5. **Wire up API/view** to dispatch command via message bus

### Repository Pattern

```python
# Abstract (domain layer)
class AbstractEventRepository(abc.ABC):
    @abc.abstractmethod
    def find_by_id(self, id: int) -> Event:
        pass

# Concrete (infrastructure layer)
class SqlAlchemyEventRepository(AbstractEventRepository):
    def find_by_id(self, id: int) -> Event:
        return self.db.session.get(Event, id)
```

### Testing Conventions

- Test files mirror source structure: `tests/service_layer/`, `tests/api/`
- Use fixtures from [`tests/conftest.py`](../tests/conftest.py)
- Database rollback per test via `base_test.py`
- Mock external services (email, geocoding)

## Gotchas

- **Generated files**: Modifications will be overwritten on next codegen run
- **Celery tasks**: Must be imported in [`project/celery_tasks.py`](../project/celery_tasks.py) to be discovered
- **Migrations**: PostGIS schema migrations sometimes need manual tweaks
- **Import order**: Domain → Service Layer → Infrastructure (avoid circular imports)
- **Deferred columns**: Some large columns use `deferred=True`, load explicitly with `.options(undefer())`

## Additional Documentation

- Deployment: [doc/deployment.md](../doc/deployment.md)
- Development setup: [doc/development.md](../doc/development.md)
- Project README: [README.md](../README.md)
