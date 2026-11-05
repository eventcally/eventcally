from project.application.queries import GetEventDetailQuery


def _refresh_dates(app, event_id):
    from project.application.commands import UpdateEventRecurringDatesCommand
    from project.domain.models.entities.actor import Actor

    app.container.cqrs.message_bus().handle(
        UpdateEventRecurringDatesCommand(actor=Actor(), event_id=event_id)
    )


def test_get_calendar_links_for_event_date(client, seeder, utils, app, db, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        with app.app_context():
            from project.infrastructure.models import Event, EventAttendanceMode
            from project.presentation.shared.event_links import (
                get_calendar_links_for_event_date,
            )
            from project.shared.dateutils import create_berlin_date

            utils.mock_now(mocker, 2020, 1, 3)

            event = db.session.get(Event, event_id)
            date_definition = event.date_definitions[0]

            date_definition.end = None
            event.attendance_mode = EventAttendanceMode.online
            event_date = event.dates[0]
            links = get_calendar_links_for_event_date(event_date)
            assert "&location" not in links["google"]

            # All-day single day
            date_definition.start = create_berlin_date(2020, 1, 2, 14, 30)
            date_definition.end = None
            date_definition.allday = True
            db.session.commit()
            _refresh_dates(app, event_id)
            db.session.expire_all()
            event_date = event.dates[0]
            links = get_calendar_links_for_event_date(event_date)
            assert "&dates=20200102/20200103&" in links["google"]

            # All-day multiple days
            date_definition.start = create_berlin_date(2020, 1, 2, 14, 30)
            date_definition.end = create_berlin_date(2020, 1, 3, 14, 30)
            date_definition.allday = True
            db.session.commit()
            _refresh_dates(app, event_id)
            db.session.expire_all()
            event_date = event.dates[0]
            links = get_calendar_links_for_event_date(event_date)
            assert "&dates=20200102/20200104&" in links["google"]


def test_get_share_links():
    from project.presentation.shared.event_links import get_share_links

    links = get_share_links("https://example.com/event/1", "Fest & Spaß")

    assert links["url"] == "https://example.com/event/1"
    assert "u=https%3A%2F%2Fexample.com%2Fevent%2F1" in links["facebook"]
    assert "text=Fest+%26+Spa%C3%9F" in links["twitter"]
    assert links["email"].startswith("mailto:?subject=")
    assert links["whatsapp"].startswith("whatsapp://send?text=")
    assert links["telegram"].startswith("https://t.me/share/url?url=")


def test_get_calendar_links_for_event(app, seeder, db):
    from project.presentation.shared.event_links import get_calendar_links_for_event

    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        event = app.container.cqrs.query_bus().handle(GetEventDetailQuery(id=event_id))
        links = get_calendar_links_for_event(event)

    assert links["ics"].endswith(f"/event/{event_id}/ical")
    assert "google" not in links


def test_calendar_link_of_an_offline_event_date_has_the_location(app, seeder, db):
    from project.application.queries import GetEventDateDetailQuery
    from project.presentation.shared.event_links import (
        get_calendar_links_for_event_date,
    )

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)
    event_date_id = seeder.get_event_date_id(event_id)

    with app.test_request_context():
        event_date = app.container.cqrs.query_bus().handle(
            GetEventDateDetailQuery(id=event_date_id)
        )
        links = get_calendar_links_for_event_date(event_date)

    assert "&location=" in links["google"]
