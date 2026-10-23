import json

import pytest

from project.domain.models.enums.event_status import EventStatus
from project.shared.dateutils import create_berlin_date

OPTIONS_URL = "/bff/manage/planning"
DATES_URL = "/bff/manage/planning/event-dates"
EXTERNAL_URL = "/bff/manage/planning/external-calendar-events"
CALENDAR_URL = "http://test.de/holidays.ics"

ICS = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//test//EN
BEGIN:VEVENT
UID:1
DTSTAMP:20201001T000000Z
SUMMARY:Holiday
DTSTART;VALUE=DATE:20201012
LOCATION:Somewhere
DESCRIPTION:Day off
END:VEVENT
END:VCALENDAR
"""


def _range(**params):
    query = dict(date_from="2020-10-01", date_to="2020-10-31")
    query.update(params)
    return "&".join(f"{k}={v}" for k, v in query.items())


def _dates_url(**params):
    return f"{DATES_URL}?{_range(**params)}"


def _names(response):
    return [i["event"]["name"] for i in response.json["items"]]


def _set_calendars(app, db, value):
    with app.app_context():
        from project.infrastructure.init_data import upsert_settings

        settings = upsert_settings()
        settings.planning_external_calendars = value
        db.session.commit()


# access


@pytest.mark.parametrize("url", [OPTIONS_URL, _dates_url()])
def test_anonymous_is_401(client, utils, url):
    assert utils.get_json(url).status_code == 401


def test_non_planner_is_403(client, seeder, utils):
    seeder.setup_base(admin_unit_verified=False)

    assert utils.get_json(OPTIONS_URL).status_code == 403
    assert utils.get_json(_dates_url()).status_code == 403
    external = (
        f"{EXTERNAL_URL}?url={CALENDAR_URL}&date_from=2020-10-01&date_to=2020-10-31"
    )
    assert utils.get_json(external).status_code == 403


# options


def test_options(client, app, db, seeder, utils):
    seeder.setup_base()
    _set_calendars(
        app,
        db,
        json.dumps([{"title": "Holidays", "url": CALENDAR_URL}, {"url": "http://b"}]),
    )

    body = utils.get_json_ok(OPTIONS_URL).json

    names = [c["name"] for c in body["categories"]]
    assert names and names == sorted(names)
    assert [d["value"] for d in body["distances"]][:2] == [500, 5000]
    assert body["external_calendars"] == [
        {"title": "Holidays", "url": CALENDAR_URL, "active": False},
        {"title": "http://b", "url": "http://b", "active": False},
    ]
    assert body["max_dates"] == 200


@pytest.mark.parametrize("value", [None, "", "not json", "[1]", "[{}]"])
def test_options_invalid_calendars_are_empty(client, app, db, seeder, utils, value):
    seeder.setup_base()
    _set_calendars(app, db, value)

    assert utils.get_json_ok(OPTIONS_URL).json["external_calendars"] == []


# event dates


def test_event_dates(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    start = create_berlin_date(2020, 10, 3, 10)
    seeder.create_event(admin_unit_id, name="Published", start=start)
    seeder.create_event(admin_unit_id, name="Planned", start=start, planned=True)
    seeder.create_event(admin_unit_id, name="Draft", start=start, draft=True)
    seeder.create_event(
        admin_unit_id, name="Later", start=create_berlin_date(2020, 11, 3, 10)
    )

    response = utils.get_json_ok(_dates_url())

    assert sorted(_names(response)) == ["Planned", "Published"]
    assert response.json["truncated"] is False
    item = next(i for i in response.json["items"] if i["event"]["name"] == "Published")
    assert item["allday"] is False
    assert item["event"]["organization_name"] == "Meine Crew"
    assert item["event"]["organizer_name"]
    assert item["event"]["place_name"]
    assert item["event"]["public_status"] == "published"
    assert item["event"]["has_status_info"] is False


def test_event_dates_last_day_is_inclusive(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id, name="Evening", start=create_berlin_date(2020, 10, 31, 20)
    )

    assert _names(utils.get_json_ok(_dates_url())) == ["Evening"]


def test_event_dates_status_info(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    start = create_berlin_date(2020, 10, 3, 10)
    seeder.create_event(admin_unit_id, name="Planned", start=start, planned=True)
    seeder.create_event(
        admin_unit_id, name="Cancelled", start=start, status=EventStatus.cancelled
    )
    seeder.create_event(admin_unit_id, name="Plain", start=start)

    items = {
        i["event"]["name"]: i["event"]
        for i in utils.get_json_ok(_dates_url()).json["items"]
    }

    assert items["Planned"]["has_status_info"] is True
    assert items["Cancelled"]["has_status_info"] is True
    assert items["Cancelled"]["status"] == "cancelled"
    assert items["Plain"]["has_status_info"] is False


def test_event_dates_category_filter(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(
        admin_unit_id, name="Other", start=create_berlin_date(2020, 10, 3, 10)
    )
    other = seeder.get_event_category_id("Other")
    unrelated = other + 1000

    both = _dates_url(category_id=other) + f"&category_id={unrelated}"

    assert _names(utils.get_json_ok(both)) == ["Other"]
    assert _names(utils.get_json_ok(_dates_url(category_id=unrelated))) == []


# Recurring dates are only generated for the future.
FUTURE = dict(date_from="2035-10-01", date_to="2035-10-31")


def test_event_dates_exclude_recurring(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    start = create_berlin_date(2035, 10, 3, 10)
    seeder.create_event(admin_unit_id, name="Single", start=start)
    seeder.create_event(
        admin_unit_id,
        name="Weekly",
        start=start,
        recurrence_rule="RRULE:FREQ=WEEKLY;COUNT=3",
    )

    everything = utils.get_json_ok(_dates_url(**FUTURE))
    assert _names(everything).count("Weekly") == 3

    single = utils.get_json_ok(_dates_url(exclude_recurring="true", **FUTURE))
    assert _names(single) == ["Single"]


def test_event_dates_postal_code(client, seeder, utils):
    from project.infrastructure.models import Location

    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(
        admin_unit_id, "Hall", location=Location(postalCode="38640")
    )
    start = create_berlin_date(2020, 10, 3, 10)
    seeder.create_event(admin_unit_id, name="InGoslar", start=start, place_id=place_id)
    seeder.create_event(admin_unit_id, name="Elsewhere", start=start)

    assert _names(utils.get_json_ok(_dates_url(postal_code="38640"))) == ["InGoslar"]


def test_event_dates_truncated(client, seeder, utils, monkeypatch):
    from project.presentation.bff.manage import planning

    monkeypatch.setattr(planning, "MAX_DATES", 2)
    monkeypatch.setattr(planning, "PAGE_SIZE", 1)
    user_id, admin_unit_id = seeder.setup_base()

    for day in (3, 4, 5):
        seeder.create_event(
            admin_unit_id, name=f"E{day}", start=create_berlin_date(2020, 10, day, 10)
        )

    body = utils.get_json_ok(_dates_url()).json

    assert [i["event"]["name"] for i in body["items"]] == ["E3", "E4"]
    assert body["truncated"] is True


@pytest.mark.parametrize(
    "params",
    [
        dict(date_from="2020-10-31", date_to="2020-10-01"),
        dict(date_from="2020-10-01", date_to="2021-01-30"),
        dict(coordinate="abc"),
        dict(distance="123"),
        dict(expected_participants_min="-1"),
    ],
)
def test_event_dates_invalid_params_are_422(client, seeder, utils, params):
    seeder.setup_base()

    assert utils.get_json(_dates_url(**params)).status_code == 422


def test_event_dates_requires_range(client, seeder, utils):
    seeder.setup_base()

    assert utils.get_json(DATES_URL).status_code == 422


def test_event_dates_location_filter(client, seeder, utils):
    seeder.setup_base()

    response = utils.get_json(_dates_url(coordinate="51.9,10.4", distance="5000"))

    utils.assert_response_ok(response)
    assert response.json["items"] == []


# external calendars


def _external(utils, url=CALENDAR_URL):
    return utils.get_json(
        f"{EXTERNAL_URL}?url={url}&date_from=2020-10-01&date_to=2020-10-31"
    )


def test_external_calendar_events(client, app, db, seeder, utils, requests_mock):
    seeder.setup_base()
    _set_calendars(app, db, json.dumps([{"url": CALENDAR_URL}]))
    requests_mock.get(CALENDAR_URL, text=ICS)

    response = _external(utils)

    utils.assert_response_ok(response)
    assert response.json["url"] == CALENDAR_URL
    (item,) = response.json["items"]
    assert item["name"] == "Holiday"
    assert item["start"] == "2020-10-12"
    assert item["allday"] is True
    assert item["location"] == "Somewhere"
    assert item["description"] == "Day off"


def test_external_calendar_unconfigured_url_is_403(
    client, app, db, seeder, utils, requests_mock
):
    seeder.setup_base()
    _set_calendars(app, db, json.dumps([{"url": CALENDAR_URL}]))
    other = requests_mock.get("http://evil.de/x.ics", text=ICS)

    assert _external(utils, "http://evil.de/x.ics").status_code == 403
    assert other.called is False


@pytest.mark.parametrize("failure", [dict(status_code=500), dict(exc=ConnectionError)])
def test_external_calendar_unreachable_is_400(
    client, app, db, seeder, utils, requests_mock, failure
):
    seeder.setup_base()
    _set_calendars(app, db, json.dumps([{"url": CALENDAR_URL}]))
    requests_mock.get(CALENDAR_URL, **failure)

    response = _external(utils)

    assert response.status_code == 400
    assert response.json["name"] == "ExternalCalendarError"
