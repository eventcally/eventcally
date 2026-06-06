import pytest

from project.domain.events.event_place_created import EventPlaceCreated
from project.domain.events.event_place_deleted import EventPlaceDeleted
from project.domain.events.event_place_updated import EventPlaceUpdated
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
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
def place(actor):
    return EventPlaceAggregate.create(actor=actor, admin_unit_id=2, name="Test Venue")


def _make_image_entity():
    return ImageEntity.from_value_object(
        ImageValueObject(data=b"img", encoding_format="image/jpeg")
    )


class TestEventPlaceAggregateCreate:
    def test_creates_instance_with_name(self, actor):
        place = EventPlaceAggregate.create(actor=actor, admin_unit_id=5, name="Venue")
        assert place.name == "Venue"
        assert place.admin_unit_id == 5

    def test_appends_created_event(self, actor):
        place = EventPlaceAggregate.create(actor=actor, admin_unit_id=5, name="Venue")
        assert len(place.domain_events) == 1
        assert isinstance(place.domain_events[0], EventPlaceCreated)

    def test_created_event_contains_name(self, actor):
        place = EventPlaceAggregate.create(actor=actor, admin_unit_id=5, name="Venue")
        assert place.domain_events[0].name == "Venue"

    def test_optional_fields_default_none(self, actor):
        place = EventPlaceAggregate.create(actor=actor, admin_unit_id=5, name="Venue")
        assert place.url is None
        assert place.description is None
        assert place.location is None
        assert place.photo is None

    def test_create_with_photo(self, actor):
        photo = _make_image_entity()
        place = EventPlaceAggregate.create(
            actor=actor, admin_unit_id=5, name="Venue", photo=photo
        )
        assert place.photo is photo
        event = place.domain_events[0]
        assert event.photo is not None


class TestEventPlaceAggregateUpdate:
    def test_update_with_no_changes_appends_no_event(self, place, actor):
        initial_count = len(place.domain_events)
        place.update(actor=actor)
        assert len(place.domain_events) == initial_count

    def test_update_name_appends_updated_event(self, place, actor):
        initial_count = len(place.domain_events)
        place.update(actor=actor, name="New Venue")
        assert len(place.domain_events) == initial_count + 1
        assert isinstance(place.domain_events[-1], EventPlaceUpdated)

    def test_update_name_sets_changed_value(self, place, actor):
        place.update(actor=actor, name="New Venue")
        event = place.domain_events[-1]
        assert isinstance(event.name, ChangedValue)
        assert event.name.old == "Test Venue"
        assert event.name.new == "New Venue"

    def test_update_description_sets_changed_value(self, place, actor):
        place.update(actor=actor, description="A great venue")
        event = place.domain_events[-1]
        assert isinstance(event.description, ChangedValue)
        assert event.description.new == "A great venue"

    def test_update_location_sets_changed_value(self, place, actor):
        loc = LocationValueObject(city="Munich")
        place.update(actor=actor, location=loc)
        event = place.domain_events[-1]
        assert isinstance(event.location, ChangedValue)
        assert event.location.new.city == "Munich"

    def test_update_photo_sets_changed_value(self, actor):
        photo = _make_image_entity()
        place = EventPlaceAggregate.create(
            actor=actor, admin_unit_id=5, name="Venue", photo=photo
        )
        new_photo = ImageEntity.from_value_object(
            ImageValueObject(data=b"new_img", encoding_format="image/png")
        )
        place.update(actor=actor, photo=new_photo)
        event = place.domain_events[-1]
        assert isinstance(event.photo, ChangedValue)
        assert event.photo.old is not None
        assert event.photo.new is not None

    def test_update_photo_to_none(self, actor):
        photo = _make_image_entity()
        place = EventPlaceAggregate.create(
            actor=actor, admin_unit_id=5, name="Venue", photo=photo
        )
        place.update(actor=actor, photo=None)
        event = place.domain_events[-1]
        assert isinstance(event.photo, ChangedValue)
        assert event.photo.new is None

    def test_update_url_sets_changed_value(self, place, actor):
        place.update(actor=actor, url="https://venue.example.com")
        event = place.domain_events[-1]
        assert isinstance(event.url, ChangedValue)
        assert event.url.new == "https://venue.example.com"


class TestEventPlaceAggregateDelete:
    def test_delete_appends_deleted_event(self, place, actor):
        initial_count = len(place.domain_events)
        place.delete(actor=actor)
        assert len(place.domain_events) == initial_count + 1
        assert isinstance(place.domain_events[-1], EventPlaceDeleted)

    def test_deleted_event_ids(self, place, actor):
        place.delete(actor=actor)
        event = place.domain_events[-1]
        assert event.id == place.id
        assert event.admin_unit_id == place.admin_unit_id
