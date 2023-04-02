import pytest


def test_update_event_dates_with_recurrence_rule(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import Event
        from project.services.event import update_event_dates_with_recurrence_rule

        event = Event.query.get(event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2030, 12, 31, 14, 30)
        date_definition.end = create_berlin_date(2030, 12, 31, 16, 30)
        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 1

        event_date = event.dates[0]
        assert event_date.start == date_definition.start
        assert event_date.end == date_definition.end

        # Update again
        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 1

        event_date = event.dates[0]
        assert event_date.start == date_definition.start
        assert event_date.end == date_definition.end

        # All-day
        date_definition.allday = True
        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 1

        event_date = event.dates[0]
        assert event_date.start == date_definition.start
        assert event_date.end == date_definition.end
        assert event_date.allday

        # Wiederholt sich alle 1 Tage, endet nach 7 Ereigniss(en)
        date_definition.recurrence_rule = "RRULE:FREQ=DAILY;COUNT=7"

        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 7


def test_update_event_dates_with_recurrence_rule_past(
    client, seeder, utils, app, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import Event
        from project.services.event import update_event_dates_with_recurrence_rule

        utils.mock_now(mocker, 2020, 1, 3)

        event = Event.query.get(event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2020, 1, 2, 14, 30)
        date_definition.end = create_berlin_date(2020, 1, 2, 16, 30)

        # Wiederholt sich alle 1 Tage, endet nach 7 Ereigniss(en)
        date_definition.recurrence_rule = "RRULE:FREQ=DAILY;COUNT=7"
        update_event_dates_with_recurrence_rule(event)

        # Es sollen nur 6 Daten vorhanden sein (das erste Date war gestern)
        len_dates = len(event.dates)
        assert len_dates == 6

        # Das erste Date ist heute
        event_date = event.dates[0]
        assert event_date.start == create_berlin_date(2020, 1, 3, 14, 30)
        assert event_date.end == create_berlin_date(2020, 1, 3, 16, 30)


def test_update_event_dates_with_recurrence_rule_past_forever(
    client, seeder, utils, app, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import Event
        from project.services.event import update_event_dates_with_recurrence_rule

        utils.mock_now(mocker, 2020, 1, 3)

        event = Event.query.get(event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2019, 1, 1, 14, 30)
        date_definition.end = create_berlin_date(2019, 1, 1, 16, 30)

        # Wiederholt sich alle 1 Tage (unendlich)
        date_definition.recurrence_rule = "RRULE:FREQ=DAILY"
        update_event_dates_with_recurrence_rule(event)

        # Es sollen 367 Daten vorhanden sein (Schaltjahr +1)
        len_dates = len(event.dates)
        assert len_dates == 367

        # Das erste Date ist heute
        event_date = event.dates[0]
        assert event_date.start == create_berlin_date(2020, 1, 3, 14, 30)
        assert event_date.end == create_berlin_date(2020, 1, 3, 16, 30)

        # Das letzte Date ist in einem Jahr
        event_date = event.dates[366]
        assert event_date.start == create_berlin_date(2021, 1, 3, 14, 30)
        assert event_date.end == create_berlin_date(2021, 1, 3, 16, 30)


def test_update_event_dates_with_recurrence_rule_exdate(
    client, seeder, utils, app, mocker
):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import Event
        from project.services.event import update_event_dates_with_recurrence_rule

        utils.mock_now(mocker, 2021, 6, 1)

        event = Event.query.get(event_id)
        date_definition = event.date_definitions[0]
        date_definition.start = create_berlin_date(2021, 4, 21, 17, 0)
        date_definition.end = create_berlin_date(2021, 4, 21, 18, 0)

        # Wiederholt sich jeden Mittwoch
        date_definition.recurrence_rule = "RRULE:FREQ=WEEKLY;BYDAY=WE;UNTIL=20211231T000000\nEXDATE:20210216T000000,20210223T000000,20210602T000000"
        update_event_dates_with_recurrence_rule(event)

        # Das erste Date soll nicht der 02.06. sein (excluded), sondern der 09.06.
        event_date = event.dates[0]
        assert event_date.start == create_berlin_date(2021, 6, 9, 17, 0)
        assert event_date.end == create_berlin_date(2021, 6, 9, 18, 0)


def test_get_meta_data(seeder, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    photo_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import Event, EventAttendanceMode, Location
        from project.services.event import get_meta_data

        event = Event.query.get(event_id)
        event.attendance_mode = EventAttendanceMode.offline

        location = Location()
        location.city = "Stadt"
        event.event_place.location = location

        event.photo_id = photo_id
        db.session.commit()

        with app.test_request_context():
            meta = get_meta_data(event)
            assert meta is not None


def test_get_recurring_events(client, seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=DAILY;COUNT=7"
    )
    seeder.create_event(admin_unit_id, recurrence_rule=None)
    seeder.create_event(admin_unit_id, recurrence_rule="")

    with app.app_context():
        from project.services.event import get_recurring_events

        recurring_events = get_recurring_events()

        assert len(recurring_events) == 1
        assert recurring_events[0].id == event_id


def test_get_events_query(client, seeder, app):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)
    seeder.upsert_event_place(admin_unit_id, "Other Place")

    with app.app_context():
        from project.services.event import get_events_query
        from project.services.event_search import EventSearchParams

        params = EventSearchParams()
        params.admin_unit_id = admin_unit_id
        params.can_read_private_events = True

        events = get_events_query(params)
        pagination = events.paginate()

        assert pagination.total == 1


@pytest.mark.parametrize(
    "index, event_descs, keyword, results, order",
    [
        (0, ("Führung durch Goslar", "Other"), "Goslar", 1, None),
        (1, ("Führung durch Goslar", "Other"), "Führung", 1, None),
        (2, ("Führung durch Goslar", "Other"), "Fuehrung", 0, None),
        (3, ("Führung durch Goslar", "Other"), "Goslar Führung", 1, None),
        (
            4,
            ("Führung durch Goslar", "Führung durch Soest"),
            "Goslar Führung",
            1,
            None,
        ),
        (
            5,
            (
                "Führung durch Goslar",
                "Führung durch Soest",
                "Führung durch Berlin",
            ),
            "Führung (Goslar OR Soest)",
            2,
            None,
        ),
    ],
)
def test_get_events_fulltext(
    client, seeder, app, index, event_descs, keyword, results, order
):
    _, admin_unit_id = seeder.setup_base()

    if type(event_descs) is not tuple:
        event_descs = [event_descs]

    event_ids = list()
    for event_desc in event_descs:
        event_id = seeder.create_event(admin_unit_id, name=event_desc)
        event_ids.append(event_id)

    with app.app_context():
        from project.services.event import get_events_query
        from project.services.event_search import EventSearchParams

        params = EventSearchParams()
        params.keyword = keyword
        events = get_events_query(params)
        pagination = events.paginate()

        assert pagination.total == results

        if not order:
            order = range(0, len(event_descs) - 1)

        i = 0
        for item in pagination.items:
            assert item.id == event_ids[order[i]]
            i = i + 1


def test_create_ical_events_for_event(client, app, db, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(
        admin_unit_id,
        recurrence_rule="RRULE:FREQ=DAILY;COUNT=10\nEXDATE:20300102T000000,20300104T000000\nRDATE:20300103T000000,20300105T000000",
    )

    with app.app_context():
        from project.models import Event, EventStatus, Location
        from project.services.event import create_ical_events_for_event

        event = Event.query.get(event_id)
        event.description = "This is a fantastic event. Watch out!"
        event.status = EventStatus.cancelled

        place = event.event_place
        place.name = "MachMitHaus Goslar"

        location = Location()
        location.street = "Markt 7"
        location.postalCode = "38640"
        location.city = "Goslar"
        location.latitude = 51.9077888
        location.longitude = 10.4333312
        place.location = location

        db.session.commit()

        with app.test_request_context():
            ical_events = create_ical_events_for_event(event)

        assert len(ical_events) == 1

        ical_event = ical_events[0]
        assert "DESCRIPTION" in ical_event
        assert "GEO" in ical_event
        assert "X-APPLE-STRUCTURED-LOCATION" in ical_event

        ical = ical_event.to_ical()
        assert ical
