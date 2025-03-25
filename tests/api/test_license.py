from tests.seeder import Seeder
from tests.utils import UtilActions


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.create_event(admin_unit_id)

    url = utils.get_url("api_v1_license_list")
    utils.get_json_ok(url)
