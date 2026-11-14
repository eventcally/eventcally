from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _assert_shell(response):
    assert b'<div id="app"' in response.data
    assert b'id="boot"' in response.data


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, name="Stadtfest")

    url = utils.get_url("main.event", event_id=event_id)
    response = utils.get_ok(url)

    _assert_shell(response)
    assert b"vue.2.6.14" not in response.data
    # The head stays server-rendered for crawlers and social cards.
    utils.assert_response_contains(response, "<title>Stadtfest</title>")
    utils.assert_response_contains(
        response,
        f'<link rel="canonical" href="http://localhost{utils.get_url("main.event", event_id=event_id)}" />',
    )
    utils.assert_response_contains(response, 'property="og:title" content="Stadtfest"')
    utils.assert_response_contains(response, 'name="twitter:card"')
    utils.assert_response_contains(response, 'application/ld+json"')
    # No-JS fallback
    utils.assert_response_contains(response, "<noscript>")
    utils.assert_response_contains(response, "<h1>Stadtfest</h1>")
    utils.assert_response_contains(response, "Beschreibung")

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

    response = utils.get(utils.get_url("main.event", event_id=1234))
    utils.assert_response_notFound(response)


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
    _assert_shell(response)
    assert b"vue.2.6.14" not in response.data

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

    response = utils.get(utils.get_url("main.event_actions", event_id=1234))
    utils.assert_response_notFound(response)


def test_delete_renders_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=event_id
    )
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_delete_is_a_shell_without_post(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=event_id
    )
    utils.get_ok(url)

    assert utils.post_form_data(url, data={}).status_code == 405


def test_delete_unknown_event(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=4711
    )
    utils.assert_response_notFound(utils.get(url))


def test_delete_event_of_other_organization(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other crew")
    event_id = seeder.create_event(other_admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_delete", id=admin_unit_id, event_id=event_id
    )
    utils.get_unauthorized(url)


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


def test_reach_log(client, seeder: Seeder, utils: UtilActions):
    import json

    from project.infrastructure.logging_config import REACH_LOGGER
    from tests.integration.log_capture import collect_lines

    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    with collect_lines(REACH_LOGGER) as lines:
        utils.get_ok(
            utils.get_url("main.event", event_id=event_id),
            headers={"Referer": "https://www.google.com/"},
        )
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["type"] == "reach"
        assert record["logger"] == REACH_LOGGER
        assert record["event_id"] == event_id
        assert record["event_date_id"] is None
        assert record["source"] == "www.google.com"
        assert record["bot"] is False
        for key in ("ip", "user_agent", "path"):
            assert key not in record

        utils.get(utils.get_url("main.event", event_id=event_id + 100))
        utils.get(utils.get_url("main.event_actions", event_id=event_id))
        assert len(lines) == 1
