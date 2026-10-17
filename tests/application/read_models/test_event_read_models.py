from datetime import datetime

from project.application.read_models.event_read_models import (
    EventDateDefinitionDetailReadModel,
    EventOrganizationReadModel,
    EventSearchItemReadModel,
)
from project.application.read_models.location_read_model import LocationReadModel


def _event(**kwargs):
    return EventSearchItemReadModel(
        id=1,
        name="Event",
        admin_unit_id=2,
        organizer_id=3,
        event_place_id=4,
        admin_unit=EventOrganizationReadModel(id=2, name="Crew"),
        **kwargs,
    )


def _definition(definition_id, start, recurrence_rule=None):
    return EventDateDefinitionDetailReadModel(
        id=definition_id, start=start, recurrence_rule=recurrence_rule
    )


def test_an_event_without_date_definitions_has_no_first_start():
    event = _event()

    assert event.min_start_definition is None
    assert event.has_multiple_dates() is False
    assert event.category is None
    assert event.photo_id is None
    assert event.custom_categories_by_set == {}


def test_the_first_start_wins_whatever_the_order():
    late = _definition(1, datetime(2040, 5, 1))
    early = _definition(2, datetime(2040, 3, 1))
    event = _event(date_definitions=[late, early])

    assert event.min_start_definition == early
    assert event.has_multiple_dates() is True


def test_recurrence_counts_as_multiple_dates():
    event = _event(
        is_recurring=True, date_definitions=[_definition(1, datetime(2040, 1, 1))]
    )

    assert event.has_multiple_dates() is True


def test_last_modified_falls_back_to_creation():
    created = datetime(2026, 1, 1)
    updated = datetime(2026, 2, 1)

    assert _event(created_at=created).last_modified_at == created
    assert _event(created_at=created, updated_at=updated).last_modified_at == updated


def test_locations_only_have_a_coordinate_with_both_values():
    assert LocationReadModel(latitude="51.9", longitude="10.4").coordinate is True
    assert LocationReadModel(latitude="51.9").coordinate is None
    assert LocationReadModel().coordinate is None
