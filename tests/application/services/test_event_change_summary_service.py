"""Unit tests for EventChangeSummaryService."""

from datetime import datetime, timezone

import pytest

from project.application.read_models.event_change_summary_read_model import (
    EventChangeSummaryReadModel,
)
from project.application.services.event_change_summary_service import (
    SIGNIFICANT_FIELDS,
    EventChangeSummaryService,
)
from project.domain import events
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_attendance_mode import EventAttendanceMode
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.types.changed_value import ChangedValue


class FakeEventReadRepo:
    def __init__(self, organizer_names=None, place_names=None):
        self._organizer_names = organizer_names or {}
        self._place_names = place_names or {}
        self.organizer_calls = []
        self.place_calls = []

    def get(self, object_id):  # pragma: no cover - unused here
        return None

    def get_organizer_names(self, object_ids):
        self.organizer_calls.append(object_ids)
        return {
            i: self._organizer_names[i]
            for i in object_ids
            if i in self._organizer_names
        }

    def get_place_names(self, object_ids):
        self.place_calls.append(object_ids)
        return {i: self._place_names[i] for i in object_ids if i in self._place_names}


def _make_event(**changes):
    return events.EventUpdated(actor=Actor(), id=1, admin_unit_id=1, **changes)


def _sample_change(field_name):
    """A ChangedValue that fits the domain event's type for the given field."""
    samples = {
        "name": ChangedValue(old="old", new="new"),
        "status": ChangedValue(old=EventStatus.scheduled, new=EventStatus.cancelled),
        "attendance_mode": ChangedValue(
            old=EventAttendanceMode.online, new=EventAttendanceMode.offline
        ),
        "booked_up": ChangedValue(old=False, new=True),
        "event_place_id": ChangedValue(old=1, new=2),
        "organizer_id": ChangedValue(old=1, new=2),
        "date_definitions": ChangedValue(
            old=[
                EventDateDefinitionValueObject(
                    start=datetime(2020, 1, 1, tzinfo=timezone.utc)
                )
            ],
            new=[
                EventDateDefinitionValueObject(
                    start=datetime(2021, 1, 1, tzinfo=timezone.utc)
                )
            ],
        ),
    }
    return samples[field_name]


class TestSignificantFields:
    def test_every_significant_field_maps_to_a_summary_field(self):
        """Guards against drift between the trigger gate and the rendered diff."""
        summary_fields = set(EventChangeSummaryReadModel.model_fields)
        event_fields = set(events.EventUpdated.model_fields)

        for event_field, summary_field in SIGNIFICANT_FIELDS.items():
            assert event_field in event_fields
            assert summary_field in summary_fields

        assert set(SIGNIFICANT_FIELDS.values()) == summary_fields


class TestHasSignificantChanges:
    def test_no_changes(self):
        service = EventChangeSummaryService(FakeEventReadRepo())
        assert service.has_significant_changes(_make_event()) is False

    @pytest.mark.parametrize("field_name", sorted(SIGNIFICANT_FIELDS.keys()))
    def test_each_significant_field(self, field_name):
        service = EventChangeSummaryService(FakeEventReadRepo())
        event = _make_event(**{field_name: _sample_change(field_name)})

        assert service.has_significant_changes(event) is True

    def test_insignificant_field_alone_does_not_count(self):
        service = EventChangeSummaryService(FakeEventReadRepo())
        event = _make_event(description=ChangedValue(old="a", new="b"))

        assert service.has_significant_changes(event) is False

    def test_does_not_query_the_read_repository(self):
        repo = FakeEventReadRepo()
        service = EventChangeSummaryService(repo)

        service.has_significant_changes(
            _make_event(organizer_id=ChangedValue(old=1, new=2))
        )

        assert repo.organizer_calls == []
        assert repo.place_calls == []


class TestBuild:
    def test_empty_event_produces_empty_summary(self):
        service = EventChangeSummaryService(FakeEventReadRepo())

        summary = service.build(_make_event())

        assert summary.has_changes() is False

    def test_resolves_organizer_and_place_names(self):
        repo = FakeEventReadRepo(
            organizer_names={1: "Old Org", 2: "New Org"},
            place_names={3: "Old Place", 4: "New Place"},
        )
        service = EventChangeSummaryService(repo)
        event = _make_event(
            organizer_id=ChangedValue(old=1, new=2),
            event_place_id=ChangedValue(old=3, new=4),
        )

        summary = service.build(event)

        assert summary.organizer.old == "Old Org"
        assert summary.organizer.new == "New Org"
        assert summary.event_place.old == "Old Place"
        assert summary.event_place.new == "New Place"

    def test_deleted_organizer_resolves_to_none(self):
        repo = FakeEventReadRepo(organizer_names={2: "New Org"})
        service = EventChangeSummaryService(repo)

        summary = service.build(_make_event(organizer_id=ChangedValue(old=1, new=2)))

        assert summary.organizer.old is None
        assert summary.organizer.new == "New Org"

    def test_names_are_resolved_in_a_single_batch_per_type(self):
        repo = FakeEventReadRepo(
            organizer_names={1: "A", 2: "B"}, place_names={3: "C", 4: "D"}
        )
        service = EventChangeSummaryService(repo)
        event = _make_event(
            organizer_id=ChangedValue(old=1, new=2),
            event_place_id=ChangedValue(old=3, new=4),
        )

        service.build(event)

        assert repo.organizer_calls == [{1, 2}]
        assert repo.place_calls == [{3, 4}]

    def test_unchanged_reference_fields_query_with_empty_sets(self):
        repo = FakeEventReadRepo()
        service = EventChangeSummaryService(repo)

        summary = service.build(_make_event(name=ChangedValue(old="a", new="b")))

        assert repo.organizer_calls == [set()]
        assert repo.place_calls == [set()]
        assert summary.organizer is None
        assert summary.event_place is None

    def test_passes_raw_values_through(self):
        service = EventChangeSummaryService(FakeEventReadRepo())
        event = _make_event(
            name=ChangedValue(old="a", new="b"),
            status=ChangedValue(old=EventStatus.scheduled, new=EventStatus.cancelled),
            attendance_mode=ChangedValue(
                old=EventAttendanceMode.online, new=EventAttendanceMode.offline
            ),
            booked_up=ChangedValue(old=False, new=True),
        )

        summary = service.build(event)

        assert summary.name.old == "a"
        assert summary.status.new == EventStatus.cancelled
        assert summary.attendance_mode.new == EventAttendanceMode.offline
        assert summary.booked_up.new is True

    def test_maps_date_definitions_to_read_models(self):
        service = EventChangeSummaryService(FakeEventReadRepo())
        old_start = datetime(2020, 1, 1, tzinfo=timezone.utc)
        new_start = datetime(2021, 1, 1, tzinfo=timezone.utc)
        event = _make_event(
            date_definitions=ChangedValue(
                old=[EventDateDefinitionValueObject(start=old_start)],
                new=[
                    EventDateDefinitionValueObject(
                        start=new_start,
                        end=datetime(2021, 1, 2, tzinfo=timezone.utc),
                        allday=True,
                        recurrence_rule="RRULE:FREQ=DAILY",
                    )
                ],
            )
        )

        summary = service.build(event)

        assert [d.start for d in summary.date_definitions.old] == [old_start]
        new_definition = summary.date_definitions.new[0]
        assert new_definition.start == new_start
        assert new_definition.allday is True
        assert new_definition.recurrence_rule == "RRULE:FREQ=DAILY"

    def test_empty_date_definition_lists_are_kept(self):
        service = EventChangeSummaryService(FakeEventReadRepo())
        event = _make_event(date_definitions=ChangedValue(old=[], new=[]))

        summary = service.build(event)

        assert summary.date_definitions.old == []
        assert summary.date_definitions.new == []
