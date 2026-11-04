from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data
    assert b"manage" in response.data


def test_update_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_update_unknown_organizer(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=4711,
    )
    utils.assert_response_notFound(utils.get(url))


def test_update_otherAdminUnit(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=other_admin_unit_id,
        event_organizer_id=organizer_id,
    )
    utils.get_unauthorized(url)


def test_organizer(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("main.organizer", id=organizer_id)
    response = utils.get_ok(url)

    assert b'id="boot"' in response.data
    assert b"<title>Meine Crew" in response.data


def test_organizer_boot_docs_url(app, client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)
    url = utils.get_url("main.organizer", id=organizer_id)

    app.config["DOCS_URL"] = None
    assert b'"docsUrl": null' in utils.get_ok(url).data

    app.config["DOCS_URL"] = "https://docs.example.org"
    assert b'"docsUrl": "https://docs.example.org"' in utils.get_ok(url).data


def test_organizer_not_found(client, seeder, utils):
    seeder.setup_base(log_in=False)

    url = utils.get_url("main.organizer", id=4711)
    utils.assert_response_notFound(utils.get(url))


def test_organizers_index_gone(client, utils):
    utils.assert_response_notFound(utils.get("/organizers"))


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("main.organizer_ical", id=admin_unit_id)
    utils.get_ok(url)


def test_list_renders_shell(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_organizers", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data


def test_list_without_permission_is_redirected(client, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_delete_url_is_gone(client, utils, seeder):
    """The delete is a modal of the list now (`POST /bff/manage/...`)."""
    _, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = f"/manage/admin_unit/{admin_unit_id}/event_organizer/{organizer_id}/delete"

    utils.assert_response_notFound(utils.get(url))
