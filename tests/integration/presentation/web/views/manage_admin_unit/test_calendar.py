from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.calendars", id=admin_unit_id)
    )

    assert b'<div id="app"' in response.data


def test_managebar_links_the_calendars(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.calendars", id=admin_unit_id)
    )

    assert f"/manage/admin_unit/{admin_unit_id}/calendars".encode() in response.data


def test_create_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.calendar_create", id=admin_unit_id)
    )

    assert b'<div id="app"' in response.data


def test_update_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.calendar_update",
            id=admin_unit_id,
            calendar_id=calendar_id,
        )
    )

    assert b'<div id="app"' in response.data


def test_update_unknown_calendar(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.calendar_update", id=admin_unit_id, calendar_id=4711
    )
    utils.assert_response_notFound(utils.get(url))


def test_update_other_admin_unit(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    calendar_id = seeder.create_calendar(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.calendar_update",
        id=other_admin_unit_id,
        calendar_id=calendar_id,
    )
    utils.get_unauthorized(url)


def test_member_without_calendar_rights_is_refused(
    client, seeder: Seeder, utils: UtilActions
):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    for endpoint in ("calendars", "calendar_create"):
        response = utils.get(
            utils.get_url(f"manage_admin_unit.{endpoint}", id=admin_unit_id)
        )
        utils.assert_response_permission_missing(
            response, "main.manage_admin_unit", id=admin_unit_id
        )
