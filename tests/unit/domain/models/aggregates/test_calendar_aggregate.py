import pytest
from pydantic import ValidationError

from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.models.entities.actor import Actor

ACTOR = Actor(user_id=1)


def _calendar(**kwargs):
    return CalendarAggregate.create(
        actor=ACTOR, admin_unit_id=1, name=kwargs.pop("name", "Name"), **kwargs
    )


def test_create_trims_name_and_defaults():
    calendar = _calendar(name="  Sports  ")

    assert calendar.id == -1
    assert calendar.name == "Sports"
    assert calendar.description is None
    assert calendar.private is False


def test_create_with_values():
    calendar = _calendar(description="Text", private=True)

    assert calendar.description == "Text"
    assert calendar.private is True


def test_create_rejects_blank_name():
    with pytest.raises(ValidationError):
        _calendar(name="   ")


def test_update_changes_fields():
    calendar = _calendar(description="Old")

    calendar.update(ACTOR, name="New", description=None, private=True)

    assert calendar.name == "New"
    assert calendar.description is None
    assert calendar.private is True


def test_update_without_values_keeps_fields():
    calendar = _calendar(description="Old")

    calendar.update(ACTOR)

    assert calendar.name == "Name"
    assert calendar.description == "Old"


def test_delete_is_allowed():
    _calendar().delete(ACTOR)


def test_entry_create_and_delete():
    entry = CalendarEntryAggregate.create(ACTOR, calendar_id=1, event_id=2)

    assert (entry.id, entry.calendar_id, entry.event_id) == (-1, 1, 2)
    entry.delete(ACTOR)
