from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("main.planning")
    response = utils.get_ok(url)

    utils.assert_response_contains(response, 'id="boot"')
    utils.assert_response_contains(response, "<title>Planungsassistent")


def test_list_can_not_use_planning(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)

    url = utils.get_url("main.planning")
    response = utils.get(url)
    utils.assert_response_permission_missing(response, "main.manage_admin_units")


def test_list_anonymous_redirects_to_login(client, utils: UtilActions):
    url = utils.get_url("main.planning")
    response = utils.get(url)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
