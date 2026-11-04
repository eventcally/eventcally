from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data
    assert b"manage" in response.data


def test_update_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_update_unknown_place(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.event_place_update", id=admin_unit_id, event_place_id=4711
    )
    utils.assert_response_notFound(utils.get(url))


def test_update_otherAdminUnit(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=other_admin_unit_id,
        event_place_id=place_id,
    )
    utils.get_unauthorized(url)


def test_create_Unauthorized(client, app, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.event_place_create", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_create_admin(client, app, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    utils.get_ok(url)


def test_list_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_places", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_delete_url_is_gone(client, utils, seeder):
    """The delete is a modal of the list now (`POST /bff/manage/...`)."""
    _, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = f"/manage/admin_unit/{admin_unit_id}/event_place/{place_id}/delete"

    utils.assert_response_notFound(utils.get(url))
