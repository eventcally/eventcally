from tests.seeder import Seeder
from tests.utils import UtilActions


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
        from project.models import ApiKey

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
