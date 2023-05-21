from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_api_access()
    url = utils.get_url("api_v1_dump")
    response = utils.get_json(url)
    utils.assert_response_notFound(response)
