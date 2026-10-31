def test_get_pagination_urls(app):
    from types import SimpleNamespace

    from project.presentation.web.views.utils import get_pagination_urls

    pagination = SimpleNamespace(
        page=2,
        pages=5,
        total=50,
        has_prev=True,
        has_next=True,
        prev_num=1,
        next_num=3,
    )

    with app.test_request_context("/eventdates?per_page=10"):
        result = get_pagination_urls(pagination)

    assert result["page"] == 2
    assert result["pages"] == 5
    assert result["total"] == 50
    assert "page=1" in result["prev_url"]
    assert "page=1" in result["first_url"]
    assert "page=3" in result["next_url"]
    assert "page=5" in result["last_url"]
    assert "per_page=10" in result["next_url"]
    assert get_pagination_urls(None) == {}


def test_handle_sql_error_without_orig():
    from sqlalchemy.exc import SQLAlchemyError

    from project.presentation.web.views.utils import handleSqlError

    assert handleSqlError(SQLAlchemyError("boom")) == "boom"


def test_truncate():
    from project.presentation.web.views.utils import truncate

    assert truncate(None, 3) is None


def _refresh_dates(app, event_id):
    from project.application.commands import UpdateEventRecurringDatesCommand
    from project.domain.models.entities.actor import Actor

    app.container.cqrs.message_bus().handle(
        UpdateEventRecurringDatesCommand(actor=Actor(), event_id=event_id)
    )


def test_get_calendar_links(client, seeder, utils, app, db, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        with app.app_context():
            from project.infrastructure.models import Event, EventAttendanceMode
            from project.presentation.web.views.utils import (
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


def test_handleBaseError():
    from project.domain.errors import BaseError
    from project.presentation.web.views.utils import handleBaseError

    class MyError(BaseError):
        def __init__(self, message):
            super().__init__(message)
            self.cause = "This is the cause of the error."

    error = MyError("Something went wrong")
    result = handleBaseError(error)
    assert result == "Something went wrong (This is the cause of the error.)"


def test_get_meta_data(seeder, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    photo_id = seeder.upsert_default_image()

    with app.app_context():
        from project.infrastructure.models import Event, EventAttendanceMode, Location
        from project.presentation.web.views.utils import get_meta_data

        event = db.session.get(Event, event_id)
        event.attendance_mode = EventAttendanceMode.offline

        location = Location()
        location.city = "Stadt"
        event.event_place.location = location

        event.photo_id = photo_id
        db.session.commit()

        with app.test_request_context():
            meta = get_meta_data(event)
            assert meta is not None


def test_create_ical_events_for_event(client, app, db, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(
        admin_unit_id,
        recurrence_rule="RRULE:FREQ=DAILY;COUNT=10\nEXDATE:20300102T000000,20300104T000000\nRDATE:20300103T000000,20300105T000000",
    )

    with app.app_context():
        from project.infrastructure.models import Event, EventStatus, Location
        from project.presentation.web.ical import create_ical_events_for_event

        event = db.session.get(Event, event_id)
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


def test_handle_sql_error_without_unique_violation():
    from types import SimpleNamespace

    from sqlalchemy.exc import SQLAlchemyError

    from project.presentation.web.views.utils import handleSqlError

    error = SQLAlchemyError("boom")
    error.orig = SimpleNamespace(message="Nope", pgcode="23503")

    assert handleSqlError(error) == "Nope"


def test_flash_errors_with_prefix(app):
    from types import SimpleNamespace

    from project.presentation.web.views.utils import flash_errors

    form = SimpleNamespace(
        errors={"name": ["Too short"]},
        name=SimpleNamespace(label=SimpleNamespace(text="Name")),
    )

    with app.test_request_context("/"):
        from flask import session

        flash_errors(form, "Place")
        flashed = session["_flashes"]

    assert flashed == [("danger", "Fehler im Feld Place Name: Too short")]


def test_flash_message_defaults_the_link_text(app):
    from project.presentation.web.views.utils import flash_message

    with app.test_request_context("/"):
        from flask import session

        flash_message("Saved", "/somewhere")
        category, message = session["_flashes"][0]

    assert category == "success"
    assert str(message) == 'Saved &ndash; <a href="/somewhere">Anzeigen</a>'
