from tests.seeder import Seeder
from tests.utils import UtilActions


def test_set_list(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_api_access(user_access=False)
    custom_event_category_set_id, _ = seeder.get_one_custom_event_category_set()

    url = utils.get_url("api_v1_custom_event_category_set_list")
    response = utils.get_json_ok(url)

    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == custom_event_category_set_id


def test_set_category_list(client, seeder: Seeder, utils: UtilActions):
    seeder.setup_api_access(user_access=False)
    custom_event_category_set_id, custom_event_category_id = (
        seeder.get_one_custom_event_category_set()
    )

    url = utils.get_url(
        "api_v1_custom_event_category_set_event_category_list",
        id=custom_event_category_set_id,
    )
    response = utils.get_json_ok(url)

    assert len(response.json["items"]) == 3
    assert response.json["items"][0]["id"] == custom_event_category_id
