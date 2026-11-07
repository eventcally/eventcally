from types import SimpleNamespace

from project.domain.models.enums.event_public_status import EventPublicStatus
from project.presentation.bff.manage.events import to_item


def _event(**overrides):
    values = dict(
        id=7,
        admin_unit_id=3,
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
    item = to_item(_event(), 3)

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

    assert to_item(_event(event_place=place), 3).place_label == "Rathaus 38640 Goslar"

    no_city = SimpleNamespace(
        name="Rathaus", location=SimpleNamespace(postalCode=None, city=None)
    )
    assert to_item(_event(event_place=no_city), 3).place_label == "Rathaus"

    no_location = SimpleNamespace(name="Rathaus", location=None)
    assert to_item(_event(event_place=no_location), 3).place_label == "Rathaus"


def test_to_item_of_a_reference_hides_internal_fields():
    owner = SimpleNamespace(name="Andere Crew")
    event = _event(
        admin_unit_id=4,
        admin_unit=owner,
        reference_id=9,
        internal_tags="geheim",
        number_of_references=2,
        number_of_reference_requests=1,
    )

    item = to_item(event, 3)

    assert item.is_reference is True
    assert item.reference_id == 9
    assert item.organization_name == "Andere Crew"
    assert item.internal_tags is None
    assert item.number_of_references is None
    assert item.number_of_reference_requests is None
