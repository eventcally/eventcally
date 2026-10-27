import datetime
import sys
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from project.domain.events.event_created import EventCreated
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.infrastructure.celery_event_dispatcher import CeleryEventDispatcher


def test_dispatch_calls_process_delayed_event_v2(monkeypatch):
    start = datetime.datetime(2026, 10, 26, 0, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    event = EventCreated(
        actor=Actor(user_id=1),
        id=1,
        admin_unit_id=2,
        name="Event",
        organizer_id=3,
        event_place_id=4,
        date_definitions=[EventDateDefinitionValueObject(start=start)],
        dates=[EventDateEntity(id=1, start=start)],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )

    fake_task = MagicMock()
    fake_base_tasks = MagicMock()
    fake_base_tasks.process_delayed_event_v2 = fake_task
    monkeypatch.setitem(
        sys.modules, "project.infrastructure.celery_base_tasks", fake_base_tasks
    )

    CeleryEventDispatcher().dispatch(event)

    expected_class_path = f"{event.__class__.__module__}.{event.__class__.__name__}"
    expected_json = event.model_dump_json(exclude_unset=True)
    fake_task.delay.assert_called_once_with(expected_class_path, expected_json)

    restored = EventCreated.model_validate_json(fake_task.delay.call_args.args[1])
    assert restored.dates[0].start == start
    assert restored.dates[0].start.tzinfo == ZoneInfo("Europe/Berlin")
    assert restored.date_definitions[0].start.tzinfo == ZoneInfo("Europe/Berlin")
