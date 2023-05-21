from tests.seeder import Seeder
from tests.utils import UtilActions


def test_organizations(client, seeder: Seeder, utils: UtilActions):
    url = utils.get_url("organizations")
    utils.get_ok(url)

    url = utils.get_url("api_v1_organization_list")
    utils.get_json_ok(url)


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("organization_ical", id=admin_unit_id)
    utils.get_ok(url)
