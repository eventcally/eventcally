import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


@pytest.mark.parametrize("type", ["search", "calendar"])
def test_custom_widget_type(client, seeder: Seeder, utils: UtilActions, type: str):
    url = utils.get_url("main.custom_widget_type", type=type)
    response = utils.get_ok(url)

    utils.assert_response_contains(response, 'id="boot"')
    utils.assert_response_contains(response, "iframeResizer.4.3.2.contentWindow.min.js")
    utils.assert_response_contains(response, "EVENTCALLY_WIDGET_SETTINGS_UPDATE_EVENT")
    # Customers embed the widget on their own sites.
    assert "X-Frame-Options" not in response.headers


def test_custom_widget_type_unknown(client, seeder: Seeder, utils: UtilActions):
    url = utils.get_url("main.custom_widget_type", type="unknown")
    utils.assert_response_notFound(utils.get(url))
