import pytest


def test_event_validate_organizer(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.models import Event, EventOrganizer

        event = Event()
        event.admin_unit_id = 1
        event.organizer = EventOrganizer(admin_unit_id=2, name="Org")

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid organizer."


def test_event_validate_place(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.models import Event, EventPlace

        event = Event()
        event.admin_unit_id = 1
        event.event_place = EventPlace(admin_unit_id=2, name="Place")

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid place."


def test_event_validate_co_organizer(client, app):
    with app.app_context():
        from sqlalchemy.exc import IntegrityError

        from project.models import Event, EventOrganizer

        event = Event()
        event.admin_unit_id = 1
        event.co_organizers = [
            EventOrganizer(admin_unit_id=2, name="Org1"),
            EventOrganizer(admin_unit_id=1, name="Org2"),
        ]

        with pytest.raises(IntegrityError) as e:
            event.validate()
        assert e.value.orig.message == "Invalid co-organizer."
