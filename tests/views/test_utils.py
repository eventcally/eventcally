import pytest


def test_send_template_mails(client, seeder, app, db, utils):
    from project.views.utils import send_template_mail

    user_id, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            send_template_mail(
                email,
                "invitation_notice",
                invitation_id=invitation_id,
                admin_unit_name="Meine Crew",
            )


def test_send_template_mail_async(client, seeder, app, db, utils):
    from project.views.utils import send_template_mail_async

    _, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            send_template_mail_async(
                email,
                "invitation_notice",
                invitation_id=invitation_id,
                admin_unit_name="Meine Crew",
            )


def test_get_pagination_urls(client, seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()

    for i in range(101):
        seeder.upsert_event_organizer(admin_unit_id, "Organizer %d" % i)

    utils.get_endpoint_ok(
        "manage_admin_unit.event_organizers", id=admin_unit_id, page=2, per_page=10
    )


def test_truncate():
    from project.views.utils import truncate

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
            from project.dateutils import create_berlin_date
            from project.models import Event, EventAttendanceMode
            from project.views.utils import get_calendar_links_for_event_date

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
    from project.views.utils import handleBaseError

    class MyError(BaseError):
        def __init__(self, message):
            super().__init__(message)
            self.cause = "This is the cause of the error."

    error = MyError("Something went wrong")
    result = handleBaseError(error)
    assert result == "Something went wrong (This is the cause of the error.)"


@pytest.mark.parametrize(
    "query_string, kwargs, expected",
    [
        ("", {}, (1, 20)),
        ("page=3&per_page=7", {}, (3, 7)),
        ("per_page=7", {"default_per_page": 50}, (1, 7)),
        ("", {"default_per_page": 50}, (1, 50)),
        ("page=2&per_page=7", {"per_page": 50}, (2, 50)),
        ("per_page=80", {"max_per_page": 50}, (1, 50)),
        ("per_page=1000", {}, (1, 100)),
    ],
)
def test_page_request_from_request_args(app, query_string, kwargs, expected):
    from project.views.utils import page_request_from_request_args

    with app.test_request_context(f"/?{query_string}"):
        page_request = page_request_from_request_args(**kwargs)

    assert (page_request.page, page_request.per_page) == expected


@pytest.mark.parametrize(
    "query_string", ["page=0", "page=-2", "page=abc", "per_page=0", "per_page=x"]
)
def test_page_request_from_request_args_aborts_on_invalid_values(app, query_string):
    from werkzeug.exceptions import NotFound

    from project.views.utils import page_request_from_request_args

    with app.test_request_context(f"/?{query_string}"):
        with pytest.raises(NotFound):
            page_request_from_request_args()


def test_abort_if_page_out_of_range():
    from werkzeug.exceptions import NotFound

    from project.application.read_models.page import Page
    from project.views.utils import abort_if_page_out_of_range

    abort_if_page_out_of_range(Page[int](items=[], page=1, per_page=20, total=0))
    abort_if_page_out_of_range(Page[int](items=[1], page=2, per_page=1, total=2))

    with pytest.raises(NotFound):
        abort_if_page_out_of_range(Page[int](items=[], page=2, per_page=20, total=3))


def test_result_or_404():
    from werkzeug.exceptions import NotFound

    from project.views.utils import result_or_404

    value = object()
    assert result_or_404(value) is value
    assert result_or_404(0) == 0
    assert result_or_404(False) is False

    with pytest.raises(NotFound):
        result_or_404(None)


def test_get_meta_data(seeder, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    photo_id = seeder.upsert_default_image()

    with app.app_context():
        from project.models import Event, EventAttendanceMode, Location
        from project.views.utils import get_meta_data

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
        from project.ical import create_ical_events_for_event
        from project.models import Event, EventStatus, Location

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
