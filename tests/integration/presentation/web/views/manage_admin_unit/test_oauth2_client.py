from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.oauth2_clients", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_create_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.oauth2_client_create", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')
    # Writing goes through the BFF.
    url = utils.get_url("manage_admin_unit.oauth2_client_create", id=admin_unit_id)
    assert utils.post_json(url, {}).status_code == 405


def test_read_and_update_are_shells(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)

    for endpoint in ("oauth2_client", "oauth2_client_update"):
        response = utils.get_endpoint_ok(
            f"manage_admin_unit.{endpoint}",
            id=admin_unit_id,
            oauth2_client_id=client_id,
        )
        utils.assert_response_contains(response, 'id="boot"')


def test_foreign_or_unknown_client(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.oauth2_client",
            id=other_admin_unit_id,
            oauth2_client_id=client_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.oauth2_client",
                id=admin_unit_id,
                oauth2_client_id=4711,
            )
        )
    )


def test_delete_page_is_gone(client, seeder: Seeder, utils: UtilActions):
    """Deleting is a modal."""
    _, admin_unit_id = seeder.setup_base()
    client_id = seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)

    utils.assert_response_notFound(
        utils.get(
            f"/manage/admin_unit/{admin_unit_id}/oauth2_client/{client_id}/delete"
        )
    )
