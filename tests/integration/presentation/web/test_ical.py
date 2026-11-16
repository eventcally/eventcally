import icalendar
import pytest

from project.infrastructure.extensions import db
from project.infrastructure.models import Location


def _setup(seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    location = Location(
        street="Seestr. 1\r\n",
        postalCode="12345",
        city="City",
        latitude=51.9,
        longitude=10.3,
    )
    place_id = seeder.upsert_event_place(
        admin_unit_id, 'Kurhaus\r\n"Hahnenklee"', location=location
    )
    event_id = seeder.create_event(
        admin_unit_id,
        name="Pfanntastisches\rHahnenklee",
        place_id=place_id,
        description="Treffpunkt: Kurhaus\r\nStart: 10.00 Uhr\r.. weiter\r\nEnde",
    )
    long_id = seeder.create_event(
        admin_unit_id,
        name="Lang",
        description="x" * 297 + "\r\n" + "y" * 50,
    )
    calendar_id = seeder.create_calendar(admin_unit_id, "Feste\rder Stadt")
    seeder.create_calendar_entry(calendar_id, event_id)
    seeder.create_calendar_entry(calendar_id, long_id)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    return admin_unit_id, organizer_id, calendar_id, event_id


def _vevents(data: bytes):
    assert data.endswith(b"\r\n")
    for line in data.split(b"\r\n"):
        assert b"\r" not in line and b"\n" not in line
    cal = icalendar.Calendar.from_ical(data)
    return cal, [c for c in cal.walk() if c.name == "VEVENT"]


@pytest.mark.parametrize(
    "endpoint", ["organization", "organizer", "calendar", "event", "event_date"]
)
def test_ical_routes_are_valid(client, seeder, utils, app, endpoint):
    admin_unit_id, organizer_id, calendar_id, event_id = _setup(seeder)
    ids = {
        "organization": admin_unit_id,
        "organizer": organizer_id,
        "calendar": calendar_id,
        "event": event_id,
        "event_date": seeder.get_event_date_id(event_id),
    }
    route = f"main.{endpoint}_ical"
    response = utils.get_ok(utils.get_url(route, id=ids[endpoint]))
    cal, vevents = _vevents(response.data)

    vevent = next(
        v for v in vevents if str(v["summary"]) == "Pfanntastisches\nHahnenklee"
    )
    assert "Start: 10.00 Uhr\n.. weiter\nEnde" in str(vevent["description"])
    location = str(vevent["location"])
    assert location.startswith("Kurhaus, 'Hahnenklee'")
    assert "Seestr. 1" in location
    apple = vevent["X-APPLE-STRUCTURED-LOCATION"]
    assert apple.params["X-ADDRESS"] == location
    assert apple.params["X-TITLE"] == location

    if endpoint == "calendar":
        assert str(cal["X-WR-CALNAME"]) == "Feste\nder Stadt"


def test_ical_truncation_keeps_no_lone_cr(client, seeder, utils):
    admin_unit_id, organizer_id, calendar_id, event_id = _setup(seeder)
    response = utils.get_ok(utils.get_url("main.organization_ical", id=admin_unit_id))
    cal, vevents = _vevents(response.data)

    long_event = next(v for v in vevents if str(v["summary"]) == "Lang")
    assert str(long_event["description"]).endswith("x" * 297 + "\n..")


def test_ical_organization_name_with_cr(client, seeder, utils, app):
    admin_unit_id, organizer_id, calendar_id, event_id = _setup(seeder)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).name = "Meine\rOrga"
        db.session.commit()

    response = utils.get_ok(utils.get_url("main.organization_ical", id=admin_unit_id))
    cal, vevents = _vevents(response.data)
    assert str(cal["X-WR-CALNAME"]) == "Meine\nOrga"
    assert str(vevents[0]["X-EVENTCALLY-ORGANIZATION"]) == "Meine\nOrga"
