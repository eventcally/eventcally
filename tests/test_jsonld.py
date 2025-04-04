import pytest


def test_get_sd_for_admin_unit(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        from project.jsonld import get_sd_for_admin_unit
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.url = "http://www.goslar.de"

        result = get_sd_for_admin_unit(admin_unit)
        assert result["url"] == "http://www.goslar.de"


def test_get_sd_for_organizer(client, app, db, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    with app.app_context():
        from project.jsonld import get_sd_for_organizer
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        organizer.email = "info@goslar.de"
        organizer.phone = "12345"
        organizer.fax = "67890"
        organizer.url = "http://www.goslar.de"

        result = get_sd_for_organizer(organizer)
        assert result["email"] == "info@goslar.de"
        assert result["phone"] == "12345"
        assert result["faxNumber"] == "67890"
        assert result["url"] == "http://www.goslar.de"


def test_get_sd_for_place(client, app, db, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from math import isclose

        from project.jsonld import get_sd_for_place
        from project.models import EventPlace, Image, Location

        place = db.session.get(EventPlace, place_id)
        place.url = "http://www.goslar.de"

        photo = Image()
        photo.data = b"something"
        photo.copyright_text = "EventCally"
        place.photo = photo

        location = Location()
        location.street = "Markt 7"
        location.postalCode = "38640"
        location.city = "Goslar"
        location.latitude = 51.9077888
        location.longitude = 10.4333312
        place.location = location

        db.session.commit()

        with app.test_request_context():
            result = get_sd_for_place(place)

        assert result["photo"] == utils.get_image_url(photo)
        assert result["url"] == "http://www.goslar.de"
        assert result["address"]["streetAddress"] == "Markt 7"
        assert result["address"]["postalCode"] == "38640"
        assert result["address"]["addressLocality"] == "Goslar"
        assert isclose(result["geo"]["latitude"], 51.9077888)
        assert isclose(result["geo"]["longitude"], 10.4333312)


def test_get_sd_for_place_noCoordinates(client, app, db, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from project.jsonld import get_sd_for_place
        from project.models import EventPlace, Location

        place = db.session.get(EventPlace, place_id)

        location = Location()
        location.street = "Markt 7"
        location.postalCode = "38640"
        location.city = "Goslar"
        place.location = location

        db.session.commit()

        result = get_sd_for_place(place)
        assert "geo" not in result


def test_get_sd_for_event_date(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.jsonld import get_sd_for_event_date
        from project.models import Event, Image
        from project.services.event import update_event

        event = db.session.get(Event, event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2030, 12, 31, 14, 30)
        date_definition.end = create_berlin_date(2030, 12, 31, 16, 30)
        event.previous_start_date = create_berlin_date(2030, 12, 30, 14, 30)
        event.external_link = "www.goslar.de"
        event.ticket_link = "www.tickets.de"
        event.accessible_for_free = True

        photo = Image()
        photo.data = b"something"
        photo.copyright_text = "EventCally"
        event.photo = photo

        update_event(event)
        db.session.commit()
        event_date = event.dates[0]

        with app.test_request_context():
            result = get_sd_for_event_date(event_date)

        assert result["startDate"] == date_definition.start
        assert result["endDate"] == date_definition.end
        assert result["previousStartDate"] == event.previous_start_date
        assert result["isAccessibleForFree"]
        assert result["url"][0] == utils.get_url("event_date", id=event_date.id)
        assert result["url"][1] == "www.goslar.de"
        assert result["url"][2] == "www.tickets.de"
        assert result["image"] == utils.get_image_url(photo)


def test_get_sd_for_event_date_allday(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.jsonld import get_sd_for_event_date
        from project.models import Event
        from project.services.event import update_event

        event = db.session.get(Event, event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2030, 12, 31, 14, 30)
        date_definition.end = create_berlin_date(2030, 12, 31, 16, 30)
        date_definition.allday = True

        update_event(event)
        db.session.commit()
        event_date = event.dates[0]

        with app.test_request_context():
            structured_data = app.json.dumps(
                get_sd_for_event_date(event_date), indent=2
            )

        assert '"startDate": "2030-12-31"' in structured_data
        assert '"endDate": "2030-12-31"' in structured_data


def test_get_sd_for_event_date_with_co_organizer(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    with app.app_context():
        from project.jsonld import get_sd_for_event_date
        from project.models import Event

        event = db.session.get(Event, event_id)
        event_date = event.dates[0]

        with app.test_request_context():
            data = get_sd_for_event_date(event_date)

        assert len(data["organizer"]) == 4


@pytest.mark.parametrize(
    "age_from, age_to, typicalAgeRange",
    [(18, None, "18-"), (None, 14, "-14"), (9, 99, "9-99")],
)
def test_get_sd_for_event_date_ageRange(
    client, app, db, seeder, utils, age_from, age_to, typicalAgeRange
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.jsonld import get_sd_for_event_date
        from project.models import Event
        from project.services.event import update_event

        event = db.session.get(Event, event_id)
        event.age_from = age_from
        event.age_to = age_to

        update_event(event)
        db.session.commit()
        event_date = event.dates[0]

        with app.test_request_context():
            result = get_sd_for_event_date(event_date)

        assert result["typicalAgeRange"] == typicalAgeRange


@pytest.mark.parametrize(
    "attendance_mode, eventAttendanceMode",
    [
        (1, "OfflineEventAttendanceMode"),
        (2, "OnlineEventAttendanceMode"),
        (3, "MixedEventAttendanceMode"),
    ],
)
def test_get_sd_for_event_date_eventAttendanceMode(
    client, app, db, seeder, utils, attendance_mode, eventAttendanceMode
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.jsonld import get_sd_for_event_date
        from project.models import Event, EventAttendanceMode
        from project.services.event import update_event

        event = db.session.get(Event, event_id)
        event.attendance_mode = EventAttendanceMode(attendance_mode)

        update_event(event)
        db.session.commit()
        event_date = event.dates[0]

        with app.test_request_context():
            result = get_sd_for_event_date(event_date)

        assert result["eventAttendanceMode"] == eventAttendanceMode


@pytest.mark.parametrize(
    "status, eventStatus",
    [
        (1, "EventScheduled"),
        (2, "EventCancelled"),
        (3, "EventMovedOnline"),
        (4, "EventPostponed"),
        (5, "EventRescheduled"),
    ],
)
def test_get_sd_for_event_date_eventStatus(
    client, app, db, seeder, utils, status, eventStatus
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.jsonld import get_sd_for_event_date
        from project.models import Event, EventStatus
        from project.services.event import update_event

        event = db.session.get(Event, event_id)
        event.status = EventStatus(status)

        update_event(event)
        db.session.commit()
        event_date = event.dates[0]

        with app.test_request_context():
            result = get_sd_for_event_date(event_date)

        assert result["eventStatus"] == eventStatus
