"""Unit tests for QueryBus — no database required."""

from typing import Optional

import pytest
from pydantic import ValidationError

from project.application.queries import PageRequest, Query
from project.application.query_bus import QueryBus
from project.domain.models.entities.actor import Actor
from tests.application.conftest import FakeAppContextProvider

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeQuery(Query[str]):
    value: int
    page: PageRequest = PageRequest()
    name: Optional[str] = None


class _FakeHandler:
    def __init__(self, result="result", error=None, on_handle=None):
        self.result = result
        self.error = error
        self.on_handle = on_handle
        self.handled = []

    def handle(self, query):
        self.handled.append(query)

        if self.on_handle:
            self.on_handle()

        if self.error:
            raise self.error

        return self.result


class _FakeQueryHandlerFactory:
    def __init__(self, handler):
        self.handler = handler
        self.requested = []

    def __call__(self, query_type):
        self.requested.append(query_type)
        return self.handler


class _FakeReadSessionScope:
    def __init__(self):
        self.entered = 0
        self.exited = 0
        self.exit_exc_types = []

    @property
    def is_active(self):
        return self.entered > self.exited

    def __enter__(self):
        self.entered += 1
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.exited += 1
        self.exit_exc_types.append(exc_type)


def _make_bus(handler=None, actor=None):
    handler = handler or _FakeHandler()
    factory = _FakeQueryHandlerFactory(handler)
    scope = _FakeReadSessionScope()
    bus = QueryBus(
        app_context_provider=FakeAppContextProvider(actor=actor),
        query_handler_factory=factory,
        read_session_scope=scope,
    )
    return bus, handler, factory, scope


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_returns_handler_result_unchanged():
    result = object()
    bus, handler, factory, _ = _make_bus(handler=_FakeHandler(result=result))

    assert bus.handle(_FakeQuery(value=1)) is result
    assert factory.requested == [_FakeQuery]


def test_fills_missing_actor_from_app_context():
    current_actor = Actor(user_id=42)
    bus, handler, _, _ = _make_bus(actor=current_actor)

    bus.handle(_FakeQuery(value=1))

    assert handler.handled[0].actor == current_actor


def test_keeps_explicit_actor():
    explicit_actor = Actor(app_installation_id=7)
    bus, handler, _, _ = _make_bus(actor=Actor(user_id=42))

    bus.handle(_FakeQuery(value=1, actor=explicit_actor))

    assert handler.handled[0].actor == explicit_actor


def test_handler_receives_validated_copy():
    bus, handler, _, _ = _make_bus()
    query = _FakeQuery(value=1, page=PageRequest(page=2, per_page=50))

    bus.handle(query)

    handled = handler.handled[0]
    assert handled is not query
    assert handled.value == 1
    assert handled.page == PageRequest(page=2, per_page=50)


def test_invalid_query_raises_before_handler_runs():
    bus, handler, factory, scope = _make_bus()
    query = _FakeQuery.model_construct(value="not an int")

    with pytest.raises(ValidationError):
        bus.handle(query)

    assert handler.handled == []
    assert factory.requested == []
    assert scope.entered == 0


def test_handler_runs_inside_read_session_scope():
    scope_states = []
    handler = _FakeHandler(on_handle=lambda: scope_states.append(scope.is_active))
    bus, _, _, scope = _make_bus(handler=handler)

    bus.handle(_FakeQuery(value=1))

    assert scope_states == [True]
    assert scope.entered == 1
    assert scope.exited == 1


def test_scope_exits_and_error_propagates_when_handler_raises():
    error = RuntimeError("boom")
    bus, _, _, scope = _make_bus(handler=_FakeHandler(error=error))

    with pytest.raises(RuntimeError) as exc_info:
        bus.handle(_FakeQuery(value=1))

    assert exc_info.value is error
    assert scope.entered == 1
    assert scope.exited == 1
    assert scope.exit_exc_types == [RuntimeError]
