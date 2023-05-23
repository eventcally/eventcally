from tests.seeder import Seeder
from tests.utils import UtilActions


def test_custom_widget_type(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("custom_widget_type", type="search", id=custom_widget_id)
    utils.get_ok(url)
