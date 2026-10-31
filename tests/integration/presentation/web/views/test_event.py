import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


@pytest.mark.parametrize(
    "external_link", [None, "https://example.com", "www.example.com"]
)
def test_read(client, seeder: Seeder, utils: UtilActions, external_link):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, external_link=external_link)

    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get_ok(url)
    assert b"vue.2.6.14" not in response.data

    event_id = seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    _, _, event_id = seeder.create_event_unverified()
    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_read_containsActionLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(
        other_user_id, "Other Crew", verified=True
    )
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get_ok(url)

    action_url = utils.get_url("main.event_actions", event_id=event_id)
    assert action_url in str(response.data)


def test_read_shows_reference_requests(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_outgoing_reference_request(admin_unit_id)

    url = utils.get_url("main.event", event_id=event_id)
    utils.get_ok(url)


def test_read_co_organizers(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id, organizer_a_id, organizer_b_id = seeder.create_event_with_co_organizers(
        admin_unit_id
    )

    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Organizer A")
    utils.assert_response_contains(response, "Organizer B")


def test_read_with_custom_category(seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    _, custom_event_category_id = seeder.get_one_custom_event_category_set()
    event_id = seeder.create_event(
        admin_unit_id, custom_category_ids={custom_event_category_id}
    )

    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Custom Category")


def test_create_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data
    assert b"manage" in response.data


def test_create_shell_anonymous_redirects_to_login(
    client, utils: UtilActions, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(log_in=False)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get(url)

    utils.assert_response_redirect_to_login(response, url)


def test_update_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_update", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_update_shell_otherAdminUnit(client, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_update", id=other_admin_unit_id, event_id=event_id
    )
    utils.get_unauthorized(url)


def test_actions(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get_ok(url)
    assert b"vue.2.6.14" not in response.data

    # Nutzer ist alleine auf der Welt. Deshalb darf es keine Referenz-Links geben
    assert b"Empfehlung anfragen" not in response.data
    assert b"Veranstaltung empfehlen" not in response.data

    event_id = seeder.create_event(admin_unit_id, draft=True)
    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    _, _, event_id = seeder.create_event_unverified()
    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_actions_withReferenceRequestLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' erlaubt: Referenz-Anfrage an andere AdminUnit
    assert b"Empfehlung anfragen" in response.data

    # Es gibt keine andere AdminUnit, bei der der aktuelle Nutzer Mitglied ist. Deshalb kann er die Veranstaltung nicht empfehlen.
    assert b"Veranstaltung empfehlen" not in response.data


def test_actions_unverifiedWithoutReferenceRequestLink(
    seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' nicht erlaubt
    assert b"Empfehlung anfragen" not in response.data


def test_actions_withReferenceLink(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(
        other_user_id, "Other Crew", verified=True
    )
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url("main.event_actions", event_id=event_id)
    response = utils.get_ok(url)

    # 'Empfehlung anfragen' nicht erlaubt: Der aktuelle Nutzer ist nicht Mitglied der anderen AdminUnit.
    assert b"Empfehlung anfragen" not in response.data

    # Referenz auf Veranstaltung der anderen AdminUnit erlaubt
    assert b"Veranstaltung empfehlen" in response.data


@pytest.mark.parametrize("db_error", [True, False])
def test_delete(client, seeder: Seeder, utils: UtilActions, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.events", id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import Event

        event = (
            Event.query.filter(Event.admin_unit_id == admin_unit_id)
            .filter(Event.name == "Name")
            .first()
        )
        assert event is None


def test_report(seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("main.event_report", event_id=event_id)
    response = utils.get_ok(url)
    assert b'id="boot"' in response.data

    url = utils.get_url("main.event_report", event_id=4711)
    utils.assert_response_notFound(utils.get(url))


def test_report_draft_anonymous(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("main.event_report", event_id=event_id)
    utils.assert_response_unauthorized(utils.get(url))


def test_report_anonymous_shell_has_no_user(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url("main.event_report", event_id=event_id)
    response = utils.get_ok(url)

    assert b'"user": null' in response.data


def test_ical(client, seeder: Seeder, utils: UtilActions):
    from project.shared.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    # Default
    event_id = seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("main.event_ical", id=event_id)
    utils.get_ok(url)

    # Draft
    draft_id = seeder.create_event(
        admin_unit_id,
        draft=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("main.event_ical", id=draft_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    utils.login()
    utils.get_ok(url)

    # Unverified
    _, _, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("main.event_ical", id=unverified_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)

    # All-day single day
    allday_id = seeder.create_event(
        admin_unit_id, allday=True, start=create_berlin_date(2020, 1, 2, 14, 30)
    )
    url = utils.get_url("main.event_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains_not(response, "DTEND;VALUE=DATE:")

    # All-day multiple days
    allday_id = seeder.create_event(
        admin_unit_id,
        allday=True,
        start=create_berlin_date(2020, 1, 2, 14, 30),
        end=create_berlin_date(2020, 1, 3, 14, 30),
    )
    url = utils.get_url("main.event_ical", id=allday_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "DTSTART;VALUE=DATE:20200102")
    utils.assert_response_contains(response, "DTEND;VALUE=DATE:20200104")

    # Recurrence rule
    event_with_recc_id = seeder.create_event(
        admin_unit_id, recurrence_rule="RRULE:FREQ=DAILY;COUNT=7"
    )
    url = utils.get_url("main.event_ical", id=event_with_recc_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "FREQ=DAILY;COUNT=7")
