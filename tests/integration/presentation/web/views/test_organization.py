from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_organizations(client, seeder: Seeder, utils: UtilActions):
    url = utils.get_url("main.organizations")
    response = utils.get_ok(url)
    utils.assert_response_contains(response, 'id="boot"')
    utils.assert_response_contains(response, "<title>Organi")

    utils.get_ok("/organizations/")

    url = utils.get_url("api_v1_organization_list")
    utils.get_json_ok(url)


def test_organization(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    url = utils.get_url("main.organization", id=admin_unit_id)
    assert url == f"/organizations/{admin_unit_id}"
    response = utils.get_ok(url)
    utils.assert_response_contains(response, 'id="boot"')
    utils.assert_response_contains(response, "Meine Crew")


def test_organization_not_found(client, utils: UtilActions):
    utils.assert_response_notFound(utils.get("/organizations/12345"))


def test_organization_old_catch_all_is_gone(client, utils: UtilActions):
    utils.assert_response_notFound(utils.get("/organizations/foo/bar"))


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("main.organization_ical", id=admin_unit_id)
    utils.get_ok(url)
