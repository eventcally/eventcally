import json

from bs4 import BeautifulSoup

from project.shared.dateutils import create_berlin_date
from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _boot(response):
    soup = BeautifulSoup(response.get_data(as_text=True), "html.parser")
    return json.loads(soup.find("script", id="boot").string)


def test_event_dates_shell(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("main.widget_event_dates", id=admin_unit_id)
    assert url == f"/organizations/{admin_unit_id}/widget/eventdates"
    response = utils.get_ok(url)

    utils.assert_response_contains(response, "iframeResizer.4.3.2.contentWindow.min.js")
    utils.assert_response_contains(response, "dist/assets")
    # Customers embed the page on their own sites.
    assert "X-Frame-Options" not in response.headers

    widget = _boot(response)["widget"]
    assert widget["organizationId"] == admin_unit_id
    settings = widget["settings"]
    assert settings["organizationId"] == admin_unit_id
    assert settings["eventsPerPage"] == 20
    assert settings["showFilter"] is True
    assert settings["showPrintButton"] is True
    assert settings["showEventCallyLink"] is False
    assert "fontFamily" not in settings
    assert "background" not in settings
    assert "buttonBackgroundColor" not in settings
    assert "linkColor" not in settings


def test_event_dates_per_page(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    def per_page(value):
        url = utils.get_url("main.widget_event_dates", id=admin_unit_id, per_page=value)
        return _boot(utils.get_ok(url))["widget"]["settings"]["eventsPerPage"]

    assert per_page(3) == 3
    assert per_page(500) == 100


def test_event_dates_styles_from_params(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    url = utils.get_url(
        "main.widget_event_dates",
        id=admin_unit_id,
        s_ft="Verdana",
        s_bg="#eceef0",
        s_pr="#b09641",
        s_li="#7b2424",
    )
    settings = _boot(utils.get_ok(url))["widget"]["settings"]

    assert settings["fontFamily"] == "Verdana"
    assert settings["background"] == "#eceef0"
    assert settings["buttonBackgroundColor"] == "#b09641"
    assert settings["buttonBorderColor"] == "#b09641"
    assert settings["linkColor"] == "#7b2424"
    assert settings["eventNameTextColor"] == "#7b2424"
    assert settings["pagingColor"] == "#7b2424"


def test_event_dates_stored_colors(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    with app.app_context():
        from colour import Color

        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.widget_font = "Verdana"
        admin_unit.widget_background_color = Color("#eceef0")
        admin_unit.widget_primary_color = Color("#b09641")
        admin_unit.widget_link_color = Color("#7b2424")
        db.session.commit()

    url = utils.get_url("main.widget_event_dates", id=admin_unit_id)
    settings = _boot(utils.get_ok(url))["widget"]["settings"]
    assert settings["fontFamily"] == "Verdana"
    assert settings["background"] == "#eceef0"
    assert settings["buttonBackgroundColor"] == "#b09641"
    assert settings["linkColor"] == "#7b2424"

    # The request wins over the stored colors.
    url = utils.get_url(
        "main.widget_event_dates", id=admin_unit_id, s_ft="Arial", s_bg="#ffffff"
    )
    settings = _boot(utils.get_ok(url))["widget"]["settings"]
    assert settings["fontFamily"] == "Arial"
    assert settings["background"] == "#ffffff"
    assert settings["buttonBackgroundColor"] == "#b09641"


def test_event_dates_not_found(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    utils.assert_response_notFound(
        utils.get(utils.get_url("main.widget_event_dates", id=4711))
    )

    for params in (
        dict(page="abc"),
        dict(page=0),
        dict(per_page="abc"),
        dict(per_page=0),
        dict(page=5),
    ):
        url = utils.get_url("main.widget_event_dates", id=admin_unit_id, **params)
        utils.assert_response_notFound(utils.get(url))


def test_event_dates_unverified(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id, _ = seeder.create_event_unverified()

    url = utils.get_url("main.widget_event_dates", id=admin_unit_id)
    utils.get_ok(url)


def test_event_dates_filters_do_not_change_status(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()
    start = create_berlin_date(2020, 10, 3, 10)
    seeder.create_event(admin_unit_id, start=start)

    for params in (
        dict(keyword="name"),
        dict(category_id=1),
        dict(date_from="2020-10-03", date_to="2021-10-03"),
        dict(date_from="garbage"),
        dict(coordinate="51.9077888,10.4333312", distance=500),
    ):
        url = utils.get_url("main.widget_event_dates", id=admin_unit_id, **params)
        utils.get_ok(url)
