from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(True)

    response = utils.get_endpoint_ok("manage_admin_unit.api_keys", id=admin_unit_id)

    utils.assert_response_contains(response, 'id="boot"')


def test_create_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(True)

    response = utils.get_endpoint_ok(
        "manage_admin_unit.api_key_create", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')
    # Writing goes through the BFF.
    url = utils.get_url("manage_admin_unit.api_key_create", id=admin_unit_id)
    assert utils.post_json(url, {}).status_code == 405


def test_read_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    response = utils.get_endpoint_ok(
        "manage_admin_unit.api_key", id=admin_unit_id, api_key_id=api_key_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_read_of_a_foreign_or_unknown_key(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.api_key",
            id=other_admin_unit_id,
            api_key_id=api_key_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.api_key", id=admin_unit_id, api_key_id=4711
            )
        )
    )


def test_update_and_delete_pages_are_gone(client, seeder: Seeder, utils: UtilActions):
    """Renaming and deleting are modals of the read page / list."""
    _, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    for action in ("update", "delete"):
        utils.assert_response_notFound(
            utils.get(
                f"/manage/admin_unit/{admin_unit_id}/api_key/{api_key_id}/{action}"
            )
        )
