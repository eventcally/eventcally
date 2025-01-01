def test_send_template_mails(client, seeder, app, db, utils):
    from project.models import AdminUnitMemberInvitation
    from project.views.utils import send_template_mail

    user_id, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            invitation = db.session.get(AdminUnitMemberInvitation, invitation_id)
            send_template_mail(
                email,
                "invitation_notice",
                invitation=invitation,
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


def test_get_calendar_links(client, seeder, utils, app, db, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    with app.test_request_context():
        with app.app_context():
            from project.dateutils import create_berlin_date
            from project.models import Event, EventAttendanceMode
            from project.services.event import update_event_dates_with_recurrence_rule
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
            update_event_dates_with_recurrence_rule(event)
            db.session.commit()
            event_date = event.dates[0]
            links = get_calendar_links_for_event_date(event_date)
            assert "&dates=20200102/20200103&" in links["google"]

            # All-day multiple days
            date_definition.start = create_berlin_date(2020, 1, 2, 14, 30)
            date_definition.end = create_berlin_date(2020, 1, 3, 14, 30)
            date_definition.allday = True
            update_event_dates_with_recurrence_rule(event)
            db.session.commit()
            event_date = event.dates[0]
            links = get_calendar_links_for_event_date(event_date)
            assert "&dates=20200102/20200104&" in links["google"]
