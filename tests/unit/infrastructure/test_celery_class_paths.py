"""Queued `process_delayed_*_v2` messages carry `module.Class` paths of events and
commands. Every path that existed before the refactor must still resolve."""

import importlib
import pkgutil
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import project.application
import project.domain
from project.application import commands
from project.application.commands.base import Command
from project.domain import events
from project.domain.events.base import Event
from project.domain.models.entities.actor import Actor
from project.infrastructure.celery_base_tasks import _load_class
from project.infrastructure.celery_command_dispatcher import CeleryCommandDispatcher
from project.infrastructure.celery_event_dispatcher import CeleryEventDispatcher

SNAPSHOT = Path(__file__).with_name("celery_class_paths.txt")


def _subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _subclasses(sub)


def _collect():
    for pkg in (project.domain, project.application):
        for info in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
            importlib.import_module(info.name)

    return {
        c
        for base in (Event, Command)
        for c in _subclasses(base)
        if c.__module__.startswith("project.")
    }


def _snapshot_paths():
    return SNAPSHOT.read_text().split()


@pytest.mark.parametrize("path", _snapshot_paths())
def test_snapshot_paths_still_resolve(path):
    _collect()

    cls = _load_class(path)

    assert issubclass(cls, (Event, Command))


def test_dispatched_classes_live_in_core():
    for cls in _collect():
        assert cls.__module__.startswith(
            ("project.domain.", "project.application.")
        ), cls


def test_command_dispatcher_writes_resolvable_paths(monkeypatch):
    import sys

    fake = MagicMock()
    monkeypatch.setitem(sys.modules, "project.infrastructure.celery_base_tasks", fake)
    command = commands.DeleteOldWebhookEventsCommand(actor=Actor())

    CeleryCommandDispatcher().dispatch(command)

    path, payload = fake.process_delayed_command_v2.delay.call_args.args
    assert _load_class(path) is type(command)
    assert type(command).model_validate_json(payload) == command


def test_event_dispatcher_writes_resolvable_paths(monkeypatch):
    import sys

    fake = MagicMock()
    monkeypatch.setitem(sys.modules, "project.infrastructure.celery_base_tasks", fake)
    event = events.Event(actor=Actor())

    CeleryEventDispatcher().dispatch(event)

    path, payload = fake.process_delayed_event_v2.delay.call_args.args
    assert _load_class(path) is type(event)
    restored = type(event).model_validate_json(payload)
    assert restored.model_dump(exclude_unset=True) == event.model_dump(
        exclude_unset=True
    )
