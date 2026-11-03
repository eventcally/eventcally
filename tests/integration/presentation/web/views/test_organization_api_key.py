from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(True)
    seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    url = utils.get_url("manage_admin_unit.api_keys", id=admin_unit_id)
    utils.get_ok(url)


def test_create(client, app, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("manage_admin_unit.api_key_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Mein API Key",
        },
    )

    with app.app_context():
        from project.infrastructure.models import ApiKey

        api_key = ApiKey.query.filter(ApiKey.admin_unit_id == admin_unit_id).first()
        assert api_key is not None

    # limit
    response = utils.get_ok(url)
    response = utils.post_form(
        url,
        response,
        {
            "name": "Mein API Key 2",
        },
    )
    utils.assert_response_error_message(
        response, "Die maximale Anzahl an API-Schlüsseln wurde erreicht."
    )


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.api_key", id=admin_unit_id, api_key_id=api_key_id
    )
    utils.get_ok(url)


def test_update(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.api_key_update", id=admin_unit_id, api_key_id=api_key_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {"name": "Neuer Name"})

    with app.app_context():
        from project.infrastructure.models import ApiKey

        assert db.session.get(ApiKey, api_key_id).name == "Neuer Name"


def test_delete(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_base(True)
    api_key_id, _ = seeder.insert_default_api_key(admin_unit_id=admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.api_key_delete", id=admin_unit_id, api_key_id=api_key_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(url, response, {"name": "Falscher Name"})
    utils.assert_response_error_message(response)

    response = utils.get_ok(url)
    response = utils.post_form(url, response, {"name": "Mein API Key"})
    utils.assert_response_redirect(
        response, "manage_admin_unit.api_keys", id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import ApiKey

        assert db.session.get(ApiKey, api_key_id) is None
