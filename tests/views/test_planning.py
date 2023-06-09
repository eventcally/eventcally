from tests.seeder import Seeder
from tests.utils import UtilActions


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("planning")
    utils.get_ok(url)


def test_list_can_not_use_planning(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)

    url = utils.get_url("planning")
    response = utils.get(url)
    utils.assert_response_permission_missing(response, "manage_admin_units")
