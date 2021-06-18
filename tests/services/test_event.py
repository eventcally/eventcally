def test_update_event_dates_with_recurrence_rule(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.dateutils import create_berlin_date
        from project.models import Event
        from project.services.event import update_event_dates_with_recurrence_rule

        event = Event.query.get(event_id)
        event.start = create_berlin_date(2030, 12, 31, 14, 30)
        event.end = create_berlin_date(2030, 12, 31, 16, 30)
        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 1

        event_date = event.dates[0]
        assert event_date.start == event.start
        assert event_date.end == event.end

        # Update again
        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 1

        event_date = event.dates[0]
        assert event_date.start == event.start
        assert event_date.end == event.end

        # Wiederholt sich alle 1 Tage, endet nach 7 Ereigniss(en)
        event.recurrence_rule = "RRULE:FREQ=DAILY;COUNT=7"

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
        event.start = create_berlin_date(2020, 1, 2, 14, 30)
        event.end = create_berlin_date(2020, 1, 2, 16, 30)

        # Wiederholt sich alle 1 Tage, endet nach 7 Ereigniss(en)
        event.recurrence_rule = "RRULE:FREQ=DAILY;COUNT=7"
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
        event.start = create_berlin_date(2019, 1, 1, 14, 30)
        event.end = create_berlin_date(2019, 1, 1, 16, 30)

        # Wiederholt sich alle 1 Tage (unendlich)
        event.recurrence_rule = "RRULE:FREQ=DAILY"
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
        event.start = create_berlin_date(2021, 4, 21, 17, 0)
        event.end = create_berlin_date(2021, 4, 21, 18, 0)

        # Wiederholt sich jeden Mittwoch
        event.recurrence_rule = "RRULE:FREQ=WEEKLY;BYDAY=WE;UNTIL=20211231T000000\nEXDATE:20210216T000000,20210223T000000,20210602T000000"
        update_event_dates_with_recurrence_rule(event)

        # Das erste Date soll nicht der 02.06. sein (excluded), sondern der 09.06.
        event_date = event.dates[0]
        assert event_date.start == create_berlin_date(2021, 6, 9, 17, 0)
        assert event_date.end == create_berlin_date(2021, 6, 9, 18, 0)


def test_get_meta_data(seeder, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event, EventAttendanceMode, Location
        from project.services.event import get_meta_data

        event = Event.query.get(event_id)
        event.attendance_mode = EventAttendanceMode.offline

        location = Location()
        location.city = "Stadt"
        event.event_place.location = location

        event.photo_id = 1

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
