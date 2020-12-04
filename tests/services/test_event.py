def test_update_event_dates_with_recurrence_rule(client, seeder, utils, app):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.app_context():
        from project.models import Event
        from project.dateutils import create_berlin_date
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

        # Wiederholt sich alle  1 Tage, endet nach 7 Ereigniss(en)
        event.recurrence_rule = "RRULE:FREQ=DAILY;COUNT=7"

        update_event_dates_with_recurrence_rule(event)

        len_dates = len(event.dates)
        assert len_dates == 7
