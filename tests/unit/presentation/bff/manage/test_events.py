from types import SimpleNamespace

from project.domain.models.enums.event_public_status import EventPublicStatus
from project.presentation.bff.manage.events import to_item


def _event(**overrides):
    values = dict(
        id=7,
        name="Konzert",
        min_start_definition=None,
        is_recurring=False,
        number_of_dates=None,
        organizer=None,
        event_place=None,
        categories=[],
        tags=None,
        internal_tags=None,
        status=None,
        public_status=EventPublicStatus.draft,
        photo=None,
        number_of_references=None,
        number_of_reference_requests=None,
        last_modified_at=None,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def test_to_item_without_optional_parts():
    item = to_item(_event())

    assert item.start is None
    assert item.allday is False
    assert item.organizer_name is None
    assert item.place_label is None
    assert item.status is None
    assert item.public_status == "draft"
    assert item.has_photo is False


def test_to_item_place_label_has_postal_code_and_city_when_known():
    location = SimpleNamespace(postalCode="38640", city="Goslar")
    place = SimpleNamespace(name="Rathaus", location=location)

    assert to_item(_event(event_place=place)).place_label == "Rathaus 38640 Goslar"

    no_city = SimpleNamespace(
        name="Rathaus", location=SimpleNamespace(postalCode=None, city=None)
    )
    assert to_item(_event(event_place=no_city)).place_label == "Rathaus"

    no_location = SimpleNamespace(name="Rathaus", location=None)
    assert to_item(_event(event_place=no_location)).place_label == "Rathaus"
