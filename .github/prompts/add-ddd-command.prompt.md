---
description: "Scaffold a new DDD command with handler and wire up message bus"
argument-hint: "Command name (e.g., PublishEvent, ArchiveOrganization)"
---

# Add DDD Command

Scaffold a complete DDD command following EventCally's architecture patterns.

## Pre-Flight Checks

1. **Verify command doesn't exist**: Search [`project/domain/commands/`](../../project/domain/commands/) for similar commands
2. **Identify return type**: Does the command return data (use `CommandWithResult`) or just mutate state (use `Command`)?
3. **Plan handler logic**: Determine required repositories and domain operations

## Steps

### 1. Create Command Class

Location: `project/domain/commands/<snake_case_name>_command.py`

**Pattern A: Command without result** (mutations only)
```python
from project.domain.types import ObjectId
from .base import Command

class DeleteEventPlaceCommand(Command):
    id: ObjectId
```

**Pattern B: Command with result** (creates/queries)
```python
from typing import Optional
from project.domain.types import ObjectId
from .base import CommandResult, CommandWithResult

class CreateEventPlaceCommandResult(CommandResult):
    id: ObjectId

class CreateEventPlaceCommand(CommandWithResult[CreateEventPlaceCommandResult]):
    admin_unit_id: ObjectId
    name: str
    url: Optional[str] = None
```

**Key points**:
- Import types from `project.domain.types`
- Inherit from `Command` or `CommandWithResult[YourResult]`
- `actor: Actor` field is auto-added by base class
- Use Pydantic field types (str, int, Optional, etc.)

### 2. Export Command

Add to [`project/domain/commands/__init__.py`](../../project/domain/commands/__init__.py):
```python
from .your_command import YourCommand, YourCommandResult  # noqa: F401
```

### 3. Create Handler

Location: `project/service_layer/command_handlers/<snake_case_name>_handler.py`

```python
from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from .abstract_command_handler import AbstractCommandHandler

class YourCommandHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.YourCommand, uow: AbstractUnitOfWork):
        with uow:
            # 1. Fetch entities from repositories
            entity = uow.your_repo.find_by_id(cmd.id)

            # 2. Call domain methods
            entity.your_action(cmd)

            # 3. Persist changes
            uow.your_repo.add(entity)  # or .remove(entity)
            uow.commit()

            # 4. Return result (if CommandWithResult)
            # return commands.YourCommandResult(id=entity.id)
```

**Handler patterns**:
- Always use `with uow:` context manager
- Load entities via repositories from `uow`
- Call domain methods on entities (pass `cmd` for audit trails)
- Commit before returning
- For `CommandWithResult`, return the result object

### 4. Export Handler

Add to [`project/service_layer/command_handlers/__init__.py`](../../project/service_layer/command_handlers/__init__.py):
```python
from .your_handler import YourCommandHandler  # noqa: F401
```

### 5. Wire Up Container

Add to [`project/container.py`](../../project/container.py) in the `command_handler_factory` FactoryAggregate (around line 375):

```python
commands.YourCommand: providers.Factory(
    command_handlers.YourCommandHandler
),
```

**With dependencies**:
```python
commands.YourCommand: providers.Factory(
    command_handlers.YourCommandHandler,
    your_service=services.your_service
),
```

Keep alphabetical order within the FactoryAggregate.

### 6. Create Tests

Location: `tests/service_layer/command_handlers/test_<snake_case_name>_handler.py`

```python
from project.domain import commands

def test_your_command(uow):
    # Arrange
    cmd = commands.YourCommand(id=1, field="value")

    # Act
    result = uow.message_bus.handle(cmd)

    # Assert
    assert result.id == 1
    # ... verify state changes
```

Use fixtures from [`tests/conftest.py`](../../tests/conftest.py). Database rolls back after each test.

## Usage After Creation

Dispatch via message bus:

```python
from flask import current_app
from project.domain import commands

# Synchronous
result = current_app.container.message_bus().handle(
    commands.YourCommand(id=1)
)

# Asynchronous (via Celery)
current_app.container.message_bus().dispatch_command(
    commands.YourCommand(id=1)
)
```

## Validation

After scaffolding:

- [ ] Run `pytest tests/service_layer/command_handlers/test_your_handler.py`
- [ ] Check `flask routes` includes endpoint if wired to API/view
- [ ] Verify imports with `pre-commit run --all-files`
- [ ] Ensure no circular imports (Domain → Service Layer → Infrastructure)

## Common Patterns

**Soft delete**:
```python
entity.delete(cmd)
uow.repo.remove(entity)
```

**Validation before action**:
```python
from .utils import ensure_entity_exists
entity = ensure_entity_exists(cmd.id, uow)
```

**Publishing domain events**:
```python
entity.publish_event(events.YourEventHappened(entity_id=entity.id))
uow.commit()  # Events dispatched after commit
```

## References

- Architecture overview: [copilot-instructions.md](../copilot-instructions.md#architecture)
- Example command: [`delete_event_place_command.py`](../../project/domain/commands/delete_event_place_command.py)
- Example handler: [`delete_event_place_handler.py`](../../project/service_layer/command_handlers/delete_event_place_handler.py)
- Unit of Work pattern: [`project/domain/abstract_unit_of_work.py`](../../project/domain/abstract_unit_of_work.py)
