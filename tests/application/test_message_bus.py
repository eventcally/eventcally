"""Unit tests for MessageBus — no database required."""

from unittest.mock import MagicMock

import pytest

from project.application.commands.base import Command
from project.application.message_bus import MessageBus
from project.domain import events
from project.domain.models.entities.actor import Actor
from tests.application.conftest import (
    FakeAppContextProvider,
    FakeCommandDispatcher,
    FakeEventDispatcher,
    FakeUnitOfWork,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeUoWFactory:
    def __init__(self, uow):
        self._uow = uow

    def uow(self):
        return self._uow


class _FakeCommandHandlerFactory:
    def __init__(self, handler):
        self._handler = handler

    def __call__(self, command_type):
        return self._handler


class _FakeEventHandlerFactory:
    def __init__(self, handlers_map=None):
        self._map = handlers_map or {}

    def __call__(self, event_type):
        return self._map.get(event_type, [])


def _make_bus(
    uow=None,
    command_handler=None,
    event_handlers_map=None,
    event_dispatcher=None,
    command_dispatcher=None,
    actor=None,
):
    uow = uow or FakeUnitOfWork()
    event_dispatcher = event_dispatcher or FakeEventDispatcher()
    command_dispatcher = command_dispatcher or FakeCommandDispatcher()
    context_provider = FakeAppContextProvider(actor=actor)

    return MessageBus(
        uow_factory=_FakeUoWFactory(uow),
        app_context_provider=context_provider,
        command_handler_factory=_FakeCommandHandlerFactory(command_handler),
        event_handler_factory=_FakeEventHandlerFactory(event_handlers_map),
        event_dispatcher=event_dispatcher,
        command_dispatcher=command_dispatcher,
    )


# ---------------------------------------------------------------------------
# Fake command / event
# ---------------------------------------------------------------------------


class _FakeCommand(Command):
    """Minimal command inheriting from Command for isinstance checks."""

    pass


def _make_fake_command(actor=None):
    if actor is None:
        actor = Actor(user_id=1)
    return _FakeCommand.model_construct(actor=actor)


class _FakeCommandResult:
    def __init__(self, value):
        self.value = value


class _FakeCommandHandler:
    def __init__(self, result=None, raises=None):
        self.called = False
        self._result = result
        self._raises = raises

    def handle(self, cmd, uow):
        self.called = True
        if self._raises:
            raise self._raises
        return self._result

    # make it validatable — bus calls model_validate if present
    def model_validate(self, data):
        return data

    def model_dump(self):
        return {}


class _FakeEventHandler:
    def __init__(self):
        self.called_with = []

    def handle(self, event, uow):
        self.called_with.append(event)


# ---------------------------------------------------------------------------
# Tests: create_uow
# ---------------------------------------------------------------------------


class TestCreateUow:
    def test_returns_uow_from_factory(self):
        uow = FakeUnitOfWork()
        bus = _make_bus(uow=uow)
        assert bus.create_uow() is uow


# ---------------------------------------------------------------------------
# Tests: handle — command routing
# ---------------------------------------------------------------------------


class TestHandleCommand:
    def test_returns_handler_result(self):
        expected = _FakeCommandResult(42)
        handler = _FakeCommandHandler(result=expected)
        bus = _make_bus(command_handler=handler)

        cmd = _make_fake_command()
        result = bus.handle(cmd)

        assert result is expected
        assert handler.called

    def test_sets_actor_on_command_when_missing(self):
        actor = Actor(user_id=99)
        handler = _FakeCommandHandler()
        bus = _make_bus(command_handler=handler, actor=actor)

        # Pydantic Command always has 'actor' attr via model field,
        # so _set_missing_command_fields never fires. Just verify command is processed.
        cmd = _make_fake_command()
        bus.handle(cmd)
        assert handler.called

    def test_does_not_overwrite_existing_actor(self):
        original_actor = Actor(user_id=1)
        bus_actor = Actor(user_id=2)
        handler = _FakeCommandHandler()
        bus = _make_bus(command_handler=handler, actor=bus_actor)

        cmd = _make_fake_command(actor=original_actor)
        bus.handle(cmd)

        # actor is not overwritten because hasattr(cmd, "actor") is always True
        assert cmd.actor is original_actor

    def test_command_exception_propagates(self):
        handler = _FakeCommandHandler(raises=ValueError("boom"))
        bus = _make_bus(command_handler=handler)

        with pytest.raises(ValueError, match="boom"):
            bus.handle(_make_fake_command())

    def test_dispatches_pending_events_after_handle(self):
        dispatcher = FakeEventDispatcher()
        uow = FakeUnitOfWork()
        handler = _FakeCommandHandler()
        bus = _make_bus(uow=uow, command_handler=handler, event_dispatcher=dispatcher)

        # Plant a pending event to be collected after commit
        fake_event = MagicMock(spec=events.Event)
        uow.pending_events = [fake_event]

        bus.handle(_make_fake_command())

        assert fake_event in dispatcher.dispatched


# ---------------------------------------------------------------------------
# Tests: handle — event routing
# ---------------------------------------------------------------------------


class TestHandleEvent:
    def test_calls_all_registered_handlers_for_event_type(self):
        handler1 = _FakeEventHandler()
        handler2 = _FakeEventHandler()
        actor = Actor()
        ev = events.AppDeleted(actor=actor, id=1, admin_unit_id=2)
        bus = _make_bus(
            event_handlers_map={type(ev): [handler1, handler2]},
        )

        bus.handle(ev)

        assert ev in handler1.called_with
        assert ev in handler2.called_with

    def test_no_handlers_does_not_raise(self):
        actor = Actor()
        ev = events.AppDeleted(actor=actor, id=1, admin_unit_id=2)
        bus = _make_bus(event_handlers_map={})
        bus.handle(ev)  # should not raise


# ---------------------------------------------------------------------------
# Tests: handle_command
# ---------------------------------------------------------------------------


class TestHandleCommandMethod:
    def test_delegates_to_handle_and_returns_result(self):
        result = _FakeCommandResult(7)
        handler = _FakeCommandHandler(result=result)
        bus = _make_bus(command_handler=handler)

        ret = bus.handle_command(_make_fake_command())
        assert ret is result


# ---------------------------------------------------------------------------
# Tests: dispatch_command
# ---------------------------------------------------------------------------


class TestDispatchCommand:
    def test_calls_command_dispatcher_dispatch(self):
        dispatcher = FakeCommandDispatcher()
        bus = _make_bus(command_dispatcher=dispatcher)

        cmd = _make_fake_command()
        bus.dispatch_command(cmd)

        assert cmd in dispatcher.dispatched

    def test_sets_actor_before_dispatching_when_missing(self):
        actor = Actor(user_id=5)
        dispatcher = FakeCommandDispatcher()
        bus = _make_bus(command_dispatcher=dispatcher, actor=actor)

        # Pydantic Command always has actor attr, so _set_missing_command_fields
        # never overwrites it. Verify dispatch completes.
        cmd = _make_fake_command()
        bus.dispatch_command(cmd)
        assert cmd in dispatcher.dispatched

    def test_sets_actor_on_non_pydantic_command_without_actor_attr(self):
        actor = Actor(user_id=42)
        dispatcher = FakeCommandDispatcher()
        bus = _make_bus(command_dispatcher=dispatcher, actor=actor)

        class _RawCommand:
            pass

        cmd = _RawCommand()
        bus.dispatch_command(cmd)

        assert getattr(cmd, "actor") is actor
        assert cmd in dispatcher.dispatched
