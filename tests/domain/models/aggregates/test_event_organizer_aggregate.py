import pytest

from project.domain.events.event_organizer_created import EventOrganizerCreated
from project.domain.events.event_organizer_deleted import EventOrganizerDeleted
from project.domain.events.event_organizer_updated import EventOrganizerUpdated
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.image_value_object import ImageValueObject
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types.changed_value import ChangedValue


@pytest.fixture
def actor():
    return Actor(user_id=1)


@pytest.fixture
def organizer(actor):
    return EventOrganizerAggregate.create(
        actor=actor, admin_unit_id=2, name="Test Organizer"
    )


def _make_image_entity():
    return ImageEntity.from_value_object(
        ImageValueObject(data=b"img", encoding_format="image/jpeg")
    )


class TestEventOrganizerAggregateCreate:
    def test_creates_instance(self, actor):
        org = EventOrganizerAggregate.create(actor=actor, admin_unit_id=2, name="Org")
        assert org.name == "Org"
        assert org.admin_unit_id == 2

    def test_appends_created_event(self, actor):
        org = EventOrganizerAggregate.create(actor=actor, admin_unit_id=2, name="Org")
        assert len(org.domain_events) == 1
        assert isinstance(org.domain_events[0], EventOrganizerCreated)

    def test_created_event_has_correct_name(self, actor):
        org = EventOrganizerAggregate.create(actor=actor, admin_unit_id=2, name="Org")
        assert org.domain_events[0].name == "Org"

    def test_optional_fields_default_none(self, actor):
        org = EventOrganizerAggregate.create(actor=actor, admin_unit_id=2, name="Org")
        assert org.url is None
        assert org.email is None
        assert org.logo is None

    def test_create_with_logo(self, actor):
        logo = _make_image_entity()
        org = EventOrganizerAggregate.create(
            actor=actor, admin_unit_id=2, name="Org", logo=logo
        )
        assert org.logo is logo
        event = org.domain_events[0]
        assert event.logo is not None


class TestEventOrganizerAggregateUpdate:
    def test_update_with_no_changes_appends_no_event(self, organizer, actor):
        initial_count = len(organizer.domain_events)
        organizer.update(actor=actor)
        assert len(organizer.domain_events) == initial_count

    def test_update_name_appends_updated_event(self, organizer, actor):
        initial_count = len(organizer.domain_events)
        organizer.update(actor=actor, name="New Name")
        assert len(organizer.domain_events) == initial_count + 1
        assert isinstance(organizer.domain_events[-1], EventOrganizerUpdated)

    def test_update_name_sets_changed_value(self, organizer, actor):
        organizer.update(actor=actor, name="New Name")
        event = organizer.domain_events[-1]
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "Test Organizer"
        assert event.name.new == "New Name"

    def test_update_url_sets_changed_value(self, organizer, actor):
        organizer.update(actor=actor, url="https://example.com")
        event = organizer.domain_events[-1]
        assert isinstance(event.url, ChangedValue)
        assert event.url.new == "https://example.com"

    def test_update_with_same_value_appends_no_event(self, organizer, actor):
        initial_count = len(organizer.domain_events)
        organizer.update(actor=actor, name="Test Organizer")
        assert len(organizer.domain_events) == initial_count

    def test_update_logo_sets_changed_value(self, actor):
        logo = _make_image_entity()
        organizer = EventOrganizerAggregate.create(
            actor=actor, admin_unit_id=2, name="Org", logo=logo
        )
        new_logo = ImageEntity.from_value_object(
            ImageValueObject(data=b"new_img", encoding_format="image/png")
        )
        organizer.update(actor=actor, logo=new_logo)
        event = organizer.domain_events[-1]
        assert isinstance(event.logo, ChangedValue)
        assert event.logo.old is not None
        assert event.logo.new is not None

    def test_update_logo_to_none_sets_changed_value(self, actor):
        logo = _make_image_entity()
        organizer = EventOrganizerAggregate.create(
            actor=actor, admin_unit_id=2, name="Org", logo=logo
        )
        organizer.update(actor=actor, logo=None)
        event = organizer.domain_events[-1]
        assert isinstance(event.logo, ChangedValue)
        assert event.logo.new is None

    def test_update_logo_unset_appends_no_event(self, actor):
        logo = _make_image_entity()
        organizer = EventOrganizerAggregate.create(
            actor=actor, admin_unit_id=2, name="Org", logo=logo
        )
        initial_count = len(organizer.domain_events)
        organizer.update(actor=actor)
        assert len(organizer.domain_events) == initial_count

    def test_update_location_sets_changed_value(self, organizer, actor):
        loc = LocationValueObject(city="Berlin")
        organizer.update(actor=actor, location=loc)
        event = organizer.domain_events[-1]
        assert isinstance(event.location, ChangedValue)
        assert event.location.new.city == "Berlin"


class TestEventOrganizerAggregateDelete:
    def test_delete_appends_deleted_event(self, organizer, actor):
        initial_count = len(organizer.domain_events)
        organizer.delete(actor=actor)
        assert len(organizer.domain_events) == initial_count + 1
        assert isinstance(organizer.domain_events[-1], EventOrganizerDeleted)

    def test_deleted_event_has_correct_ids(self, organizer, actor):
        organizer.delete(actor=actor)
        event = organizer.domain_events[-1]
        assert event.id == organizer.id
        assert event.admin_unit_id == organizer.admin_unit_id
