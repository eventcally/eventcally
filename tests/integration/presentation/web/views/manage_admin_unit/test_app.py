from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok("manage_admin_unit.apps", id=admin_unit_id)

    utils.assert_response_contains(response, 'id="boot"')


def test_create_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok("manage_admin_unit.app_create", id=admin_unit_id)

    utils.assert_response_contains(response, 'id="boot"')
    # Writing goes through the BFF.
    url = utils.get_url("manage_admin_unit.app_create", id=admin_unit_id)
    assert utils.post_json(url, {}).status_code == 405


def test_read_and_update_are_shells(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    for endpoint in ("app", "app_update"):
        response = utils.get_endpoint_ok(
            f"manage_admin_unit.{endpoint}", id=admin_unit_id, app_id=app_id
        )
        utils.assert_response_contains(response, 'id="boot"')


def test_foreign_or_unknown_app(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url("manage_admin_unit.app", id=other_admin_unit_id, app_id=app_id)
    )
    utils.assert_response_notFound(
        utils.get(utils.get_url("manage_admin_unit.app", id=admin_unit_id, app_id=4711))
    )


def test_removed_pages_are_gone(client, seeder: Seeder, utils: UtilActions):
    """Deleting an app is a modal; its keys are a section of the read page."""
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    key_id = seeder.insert_app_key(app_id)[1]
    base = f"/manage/admin_unit/{admin_unit_id}/app/{app_id}"

    for path in (
        "delete",
        "app_keys",
        "app_key/create",
        f"app_key/{key_id}",
        f"app_key/{key_id}/delete",
    ):
        utils.assert_response_notFound(utils.get(f"{base}/{path}"))
