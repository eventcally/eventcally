from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _setup_with_events(seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id, "Stadtfeste")
    published = seeder.create_event(admin_unit_id, name="Sichtbar")
    draft = seeder.create_event(admin_unit_id, name="Entwurf", draft=True)
    seeder.create_calendar_entry(calendar_id, published)
    seeder.create_calendar_entry(calendar_id, draft)
    return user_id, admin_unit_id, calendar_id


def test_calendar_shell_with_head(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id, "Stadtfeste")
    from project.infrastructure.extensions import db
    from project.infrastructure.models import Calendar

    with client.application.app_context():
        db.session.get(Calendar, calendar_id).description = "Alle Feste der Stadt"
        db.session.commit()

    url = utils.get_url("main.calendar", id=calendar_id)
    assert url == f"/calendars/{calendar_id}"
    response = utils.get_ok(url)

    utils.assert_response_contains(response, 'id="boot"')
    utils.assert_response_contains(response, "<title>Stadtfeste")
    utils.assert_response_contains(response, "Alle Feste der Stadt")
    utils.assert_response_contains(
        response,
        f'<link rel="canonical" href="http://localhost/calendars/{calendar_id}"',
    )


def test_calendar_without_description(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id)

    response = utils.get_ok(utils.get_url("main.calendar", id=calendar_id))

    utils.assert_response_contains(response, "Calendar – Meine Crew")


def test_calendar_not_found(client, utils: UtilActions):
    utils.assert_response_notFound(utils.get("/calendars/12345"))
    utils.assert_response_notFound(utils.get("/calendars/12345/ical"))


def test_private_calendar_is_404_without_calendars_read(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    calendar_id = seeder.create_calendar(admin_unit_id, private=True)

    utils.assert_response_notFound(utils.get(f"/calendars/{calendar_id}"))

    seeder.create_user("other@test.de")
    utils.login("other@test.de")
    utils.assert_response_notFound(utils.get(f"/calendars/{calendar_id}"))


def test_private_calendar_renders_for_members_with_calendars_read(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id, private=True)

    utils.get_ok(f"/calendars/{calendar_id}")


def test_ical_lists_only_public_events(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id, calendar_id = _setup_with_events(seeder)

    response = utils.get_ok(utils.get_url("main.calendar_ical", id=calendar_id))

    assert response.mimetype == "text/calendar"
    assert f"calendar_{calendar_id}.ics" in response.headers["Content-disposition"]
    body = response.data.decode()
    assert "X-WR-CALNAME:Stadtfeste" in body
    assert "SUMMARY:Sichtbar" in body
    assert "Entwurf" not in body


def test_ical_of_private_calendar_is_404_even_for_members(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id, private=True)

    utils.assert_response_notFound(utils.get(f"/calendars/{calendar_id}/ical"))
