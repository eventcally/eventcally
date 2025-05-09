from tests.seeder import Seeder
from tests.utils import UtilActions


def test_list(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(True)
    seeder.insert_default_api_key(user_id)

    url = utils.get_url("manage_admin_unit.api_keys", id=admin_unit_id)
    utils.get_ok(url)
