from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.app_installations", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_read_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)

    response = utils.get_endpoint_ok(
        "manage_admin_unit.app_installation",
        id=admin_unit_id,
        app_installation_id=installation_id,
    )
    utils.assert_response_contains(response, 'id="boot"')

    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app_installation",
            id=other_admin_unit_id,
            app_installation_id=installation_id,
        )
    )


def test_install_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=other_admin_unit_id)
    url = utils.get_url(
        "manage_admin_unit.app_installations_install",
        id=admin_unit_id,
        app_id=app_id,
    )

    response = utils.get_ok(url)

    utils.assert_response_contains(response, 'id="boot"')
    # Installing goes through the BFF.
    assert utils.post_json(url, {}).status_code == 405


def test_install_of_an_unknown_app_is_not_found(client, seeder: Seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app_installations_install",
                id=admin_unit_id,
                app_id=4711,
            )
        )
    )


def test_removed_pages_are_gone(client, seeder: Seeder, utils: UtilActions):
    """Uninstalling is a modal; accepting permissions is part of the read page."""
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)
    base = f"/manage/admin_unit/{admin_unit_id}/app_installation/{installation_id}"

    for path in ("delete", "accept_permissions"):
        utils.assert_response_notFound(utils.get(f"{base}/{path}"))
