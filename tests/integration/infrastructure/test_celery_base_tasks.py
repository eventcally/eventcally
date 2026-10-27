import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from project.domain.events.event_created import EventCreated
from project.domain.events.event_updated import EventUpdated
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.event_date_entity import EventDateEntity
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types.changed_value import ChangedValue

berlin = ZoneInfo("Europe/Berlin")


def _run(app, event):
    from project.infrastructure.celery_app import celery

    path = f"{event.__class__.__module__}.{event.__class__.__name__}"
    task = celery.tasks["project.base_tasks.process_delayed_event_v2"]
    handled = []
    with app.app_context():
        message_bus = app.container.cqrs.message_bus()
        with patch.object(
            type(message_bus), "handle", lambda self, e: handled.append(e)
        ):
            result = task.apply(args=[path, event.model_dump_json(exclude_unset=True)])
    return result, handled


def _dates(*starts):
    return [
        EventDateEntity(id=i, start=s, end=s + datetime.timedelta(hours=2))
        for i, s in enumerate(starts, start=1)
    ]


def _definitions(*starts):
    return [EventDateDefinitionValueObject(start=s) for s in starts]


def test_process_delayed_event_v2_event_created(app, db):
    starts = [
        datetime.datetime(2026, 10, 24, 20, 0, tzinfo=berlin),
        datetime.datetime(2026, 10, 26, 20, 0, tzinfo=berlin),
    ]
    event = EventCreated(
        actor=Actor(user_id=1),
        id=1,
        admin_unit_id=1,
        name="Event",
        organizer_id=1,
        event_place_id=1,
        date_definitions=_definitions(*starts),
        dates=_dates(*starts),
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )

    result, handled = _run(app, event)

    assert result.successful(), result.result
    assert len(handled) == 1
    assert [d.start for d in handled[0].dates] == starts
    assert all(isinstance(d.start.tzinfo, ZoneInfo) for d in handled[0].dates)


def test_process_delayed_event_v2_event_updated(app, db):
    old = [datetime.datetime(2026, 10, 24, 20, 0, tzinfo=berlin)]
    new = [datetime.datetime(2026, 10, 26, 20, 0, tzinfo=berlin)]
    event = EventUpdated(
        actor=Actor(user_id=1),
        id=1,
        admin_unit_id=1,
        dates=ChangedValue(old=_dates(*old), new=_dates(*new)),
        date_definitions=ChangedValue(old=_definitions(*old), new=_definitions(*new)),
    )

    result, handled = _run(app, event)

    assert result.successful(), result.result
    assert handled[0].dates.new[0].start == new[0]
    assert isinstance(handled[0].dates.old[0].start.tzinfo, ZoneInfo)
