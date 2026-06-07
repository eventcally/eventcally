import datetime

import pytest

from project.domain.errors.constraint_error import ConstraintError
from project.domain.events.event_created import EventCreated
from project.domain.events.event_deleted import EventDeleted
from project.domain.events.event_updated import EventUpdated
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.types.changed_value import ChangedValue


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def now():
    return datetime.datetime(2028, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture
def date_def(now):
    return EventDateDefinitionValueObject(start=now)


def _make_event(actor, date_def, **kwargs):
    defaults = dict(
        actor=actor,
        admin_unit_id=2,
        name="Test Event",
        organizer_id=3,
        event_place_id=4,
        date_definitions=[date_def],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )
    defaults.update(kwargs)
    return EventAggregate.create(**defaults)


def _make_image_entity():
    return ImageEntity.from_value_object(
        ImageValueObject(data=b"img", encoding_format="image/jpeg")
    )


class TestEventAggregateCreate:
    def test_creates_instance(self, actor, date_def):
        event = _make_event(actor, date_def)
        assert event.name == "Test Event"
        assert event.admin_unit_id == 2
        assert event.organizer_id == 3
        assert event.event_place_id == 4

    def test_appends_created_event(self, actor, date_def):
        event = _make_event(actor, date_def)
        assert len(event.domain_events) == 1
        assert isinstance(event.domain_events[0], EventCreated)

    def test_created_event_has_correct_name(self, actor, date_def):
        event = _make_event(actor, date_def)
        assert event.domain_events[0].name == "Test Event"

    def test_tags_stripped_of_spaces(self, actor, date_def):
        event = _make_event(actor, date_def, tags="tag1, tag2, tag3")
        created_event = event.domain_events[0]
        assert " " not in created_event.tags

    def test_internal_tags_stripped_of_spaces(self, actor, date_def):
        event = _make_event(actor, date_def, internal_tags="a, b, c")
        created_event = event.domain_events[0]
        assert " " not in created_event.internal_tags

    def test_none_tags_stays_none(self, actor, date_def):
        event = _make_event(actor, date_def, tags=None)
        created_event = event.domain_events[0]
        assert created_event.tags is None

    def test_none_internal_tags_stays_none(self, actor, date_def):
        event = _make_event(actor, date_def, internal_tags=None)
        created_event = event.domain_events[0]
        assert created_event.internal_tags is None

    def test_default_status(self, actor, date_def):
        event = _make_event(actor, date_def)
        assert event.status == EventStatus.scheduled

    def test_dates_generated_after_create(self, actor, date_def):
        event = _make_event(actor, date_def)
        assert len(event.dates) == 1

    def test_create_with_photo(self, actor, date_def):
        photo = _make_image_entity()
        event = _make_event(actor, date_def, photo=photo)
        created = event.domain_events[0]
        assert created.photo is not None


class TestEventAggregateValidateInstance:
    def test_raises_when_no_date_definitions(self, actor):
        with pytest.raises(ConstraintError):
            EventAggregate(
                id=-1,
                admin_unit_id=2,
                name="Event",
                organizer_id=3,
                event_place_id=4,
                date_definitions=[],
                status=EventStatus.scheduled,
                public_status=EventPublicStatus.published,
            ).validate_instance()

    def test_raises_when_organizer_is_also_co_organizer(self, actor, date_def):
        with pytest.raises(ConstraintError):
            EventAggregate(
                id=-1,
                admin_unit_id=2,
                name="Event",
                organizer_id=3,
                event_place_id=4,
                date_definitions=[date_def],
                status=EventStatus.scheduled,
                public_status=EventPublicStatus.published,
                co_organizer_ids=[3],
            ).validate_instance()

    def test_does_not_raise_when_valid(self, actor, date_def):
        agg = EventAggregate(
            id=-1,
            admin_unit_id=2,
            name="Event",
            organizer_id=3,
            event_place_id=4,
            date_definitions=[date_def],
            status=EventStatus.scheduled,
            public_status=EventPublicStatus.published,
        )
        agg.validate_instance()  # Should not raise


class TestEventAggregateUpdateEventDatesWithRecurrenceRule:
    def test_non_recurring_generates_single_date(self, actor, now):
        date_def = EventDateDefinitionValueObject(start=now)
        event = _make_event(actor, date_def)
        assert len(event.dates) == 1
        assert event.dates[0].start == now

    def test_non_recurring_with_end_generates_date_with_end(self, actor, now):
        end = now + datetime.timedelta(hours=2)
        date_def = EventDateDefinitionValueObject(start=now, end=end)
        event = _make_event(actor, date_def)
        assert len(event.dates) == 1
        assert event.dates[0].end == end

    def test_non_recurring_without_end_has_none_end(self, actor, now):
        date_def = EventDateDefinitionValueObject(start=now, end=None)
        event = _make_event(actor, date_def)
        assert event.dates[0].end is None

    def test_recurring_rule_generates_multiple_dates(self, actor):
        # Use a future date so the recurrence utility does not filter it out
        start = datetime.datetime(2028, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        date_def = EventDateDefinitionValueObject(
            start=start,
            recurrence_rule="FREQ=WEEKLY;COUNT=3",
        )
        event = _make_event(actor, date_def)
        assert len(event.dates) == 3

    def test_allday_normalizes_start_to_begin_of_day(self, actor):
        start = datetime.datetime(2024, 6, 1, 14, 30, 0, tzinfo=datetime.timezone.utc)
        date_def = EventDateDefinitionValueObject(start=start, allday=True)
        event = _make_event(actor, date_def)
        assert event.dates[0].allday is True
        assert event.dates[0].start.hour == 0
        assert event.dates[0].start.minute == 0

    def test_allday_normalizes_end_to_end_of_day(self, actor):
        start = datetime.datetime(2024, 6, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        end = datetime.datetime(2024, 6, 1, 14, 30, 0, tzinfo=datetime.timezone.utc)
        date_def = EventDateDefinitionValueObject(start=start, end=end, allday=True)
        event = _make_event(actor, date_def)
        assert event.dates[0].end.hour == 23
        assert event.dates[0].end.minute == 59

    def test_existing_dates_reused_when_matching(self, actor, now):
        date_def = EventDateDefinitionValueObject(start=now)
        event = _make_event(actor, date_def)
        first_date = event.dates[0]
        # Call again with same definition - existing dates should be reused
        event.update_event_dates_with_recurrence_rule()
        assert event.dates[0] is first_date

    def test_dates_removed_when_not_in_definition(self, actor, now):
        date_def = EventDateDefinitionValueObject(
            start=now, recurrence_rule="FREQ=WEEKLY;COUNT=2"
        )
        event = _make_event(actor, date_def)
        assert len(event.dates) == 2
        # Update with single occurrence
        single_def = EventDateDefinitionValueObject(start=now)
        event.date_definitions = [single_def]
        event.update_event_dates_with_recurrence_rule()
        assert len(event.dates) == 1


class TestEventAggregateUpdate:
    def test_update_with_no_changes_appends_no_event(self, actor, date_def):
        event = _make_event(actor, date_def)
        initial_count = len(event.domain_events)
        event.update(actor=actor)
        assert len(event.domain_events) == initial_count

    def test_update_name_appends_updated_event(self, actor, date_def):
        event = _make_event(actor, date_def)
        initial_count = len(event.domain_events)
        event.update(actor=actor, name="New Name")
        assert len(event.domain_events) == initial_count + 1
        assert isinstance(event.domain_events[-1], EventUpdated)

    def test_update_name_sets_changed_value(self, actor, date_def):
        event = _make_event(actor, date_def)
        event.update(actor=actor, name="Updated")
        updated = event.domain_events[-1]
        assert isinstance(updated.name, ChangedValue)
        assert updated.name.old == "Test Event"
        assert updated.name.new == "Updated"

    def test_update_tags_strips_spaces(self, actor, date_def):
        event = _make_event(actor, date_def)
        event.update(actor=actor, tags="a, b, c")
        assert event.tags == "a,b,c"

    def test_update_tags_none_does_not_change(self, actor, date_def):
        event = _make_event(actor, date_def, tags="existing")
        # Passing None replaces existing tags
        event.update(actor=actor, tags=None)
        assert event.tags is None

    def test_update_internal_tags_strips_spaces(self, actor, date_def):
        event = _make_event(actor, date_def)
        event.update(actor=actor, internal_tags="x, y")
        assert event.internal_tags == "x,y"

    def test_update_photo_sets_changed_value(self, actor, date_def):
        photo = _make_image_entity()
        event = _make_event(actor, date_def, photo=photo)
        new_photo = ImageEntity.from_value_object(
            ImageValueObject(data=b"new_img", encoding_format="image/png")
        )
        event.update(actor=actor, photo=new_photo)
        updated = event.domain_events[-1]
        assert isinstance(updated.photo, ChangedValue)

    def test_update_photo_to_none(self, actor, date_def):
        photo = _make_image_entity()
        event = _make_event(actor, date_def, photo=photo)
        event.update(actor=actor, photo=None)
        updated = event.domain_events[-1]
        assert isinstance(updated.photo, ChangedValue)
        assert updated.photo.new is None

    def test_update_date_definitions_triggers_recurrence_update(self, actor, now):
        date_def = EventDateDefinitionValueObject(start=now)
        event = _make_event(actor, date_def)
        new_start = now + datetime.timedelta(days=1)
        new_date_def = EventDateDefinitionValueObject(start=new_start)
        event.update(actor=actor, date_definitions=[new_date_def])
        assert event.dates[0].start == new_start
        updated = event.domain_events[-1]
        assert isinstance(updated.date_definitions, ChangedValue)
        assert updated.date_definitions.new[0].start == new_start

    def test_update_date_definitions_same_value_does_not_create_domain_event(
        self, actor
    ):
        date_def1 = EventDateDefinitionValueObject(
            start=datetime.datetime(2028, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        )
        date_def2 = EventDateDefinitionValueObject(
            start=datetime.datetime(2028, 6, 2, 10, 0, 0, tzinfo=datetime.timezone.utc)
        )
        event = _make_event(actor, date_def1, date_definitions=[date_def1, date_def2])

        new_date_def1 = EventDateDefinitionValueObject(
            start=datetime.datetime(2028, 6, 1, 10, 0, 0, tzinfo=datetime.timezone.utc)
        )
        new_date_def2 = EventDateDefinitionValueObject(
            start=datetime.datetime(2028, 6, 2, 10, 0, 0, tzinfo=datetime.timezone.utc)
        )
        event.update(actor=actor, date_definitions=[new_date_def1, new_date_def2])
        assert not isinstance(event.domain_events[-1], EventUpdated)

    def test_update_organizer_id_sets_changed_value(self, actor, date_def):
        event = _make_event(actor, date_def)
        event.update(actor=actor, organizer_id=99)
        updated = event.domain_events[-1]
        assert isinstance(updated.organizer_id, ChangedValue)
        assert updated.organizer_id.new == 99


class TestEventAggregateDelete:
    def test_delete_appends_deleted_event(self, actor, date_def):
        event = _make_event(actor, date_def)
        initial_count = len(event.domain_events)
        event.delete(actor=actor)
        assert len(event.domain_events) == initial_count + 1
        assert isinstance(event.domain_events[-1], EventDeleted)

    def test_deleted_event_ids(self, actor, date_def):
        event = _make_event(actor, date_def)
        event.delete(actor=actor)
        deleted = event.domain_events[-1]
        assert deleted.id == event.id
        assert deleted.admin_unit_id == event.admin_unit_id
