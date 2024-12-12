from tests.seeder import Seeder
from tests.utils import UtilActions


def test_event_dates(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)
    seeder.create_event(admin_unit_id, draft=True)

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "widget.css")
    assert "X-Frame-Options" not in response.headers

    event_url = utils.get_url("event_date", id=1)
    utils.assert_response_contains(response, event_url)

    draft_url = utils.get_url("event_date", id=2)
    utils.assert_response_contains_not(response, draft_url)

    url = utils.get_url("widget_event_dates", id=admin_unit_id, keyword="name")
    utils.get_ok(url)

    url = utils.get_url("widget_event_dates", id=admin_unit_id, category_id=1)
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        coordinate="51.9077888,10.4333312",
        distance=500,
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        date_from="2020-10-03",
        date_to="2021-10-03",
    )
    utils.get_ok(url)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        s_ft="Verdana",
        s_bg="#eceef0",
        s_pr="#b09641",
        s_li="#7b2424",
    )
    utils.get_ok(url)

    # Unverified
    _, unverified_admin_unit_id, unverified_id = seeder.create_event_unverified()
    url = utils.get_url("widget_event_dates", id=unverified_admin_unit_id)
    response = utils.get_ok(url)

    unverified_date_id = seeder.get_event_date_id(unverified_id)
    unverified_url = utils.get_url("event_date", id=unverified_date_id)
    utils.assert_response_contains_not(response, unverified_url)


def test_event_dates_oneDay(client, seeder, utils):
    from project.dateutils import create_berlin_date

    user_id, admin_unit_id = seeder.setup_base()

    start = create_berlin_date(2020, 10, 3, 10)
    end = create_berlin_date(2020, 10, 3, 11)
    name = "Spezialveranstaltung"
    seeder.create_event(admin_unit_id, name=name, start=start, end=end)

    url = utils.get_url(
        "widget_event_dates",
        id=admin_unit_id,
        date_from="2020-10-03",
        date_to="2020-10-03",
    )
    response = utils.get_ok(url)
    utils.assert_response_contains(response, name)


def test_event_dates_noneDescription(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id, description=None)

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    utils.get_ok(url)


def get_create_data():
    return {
        "accept_tos": "y",
        "name": "Vorschlag",
        "start": ["2030-12-31", "23:59"],
        "contact_name": "Vorname Nachname",
        "contact_email": "vorname@nachname.de",
        "contact_email_notice": "y",
        "event_place_id": "Freitext Ort",
        "organizer_id": "Freitext Organisator",
    }


def test_event_dates_colors(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    seeder.create_event(admin_unit_id)

    with app.app_context():
        from colour import Color

        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.widget_font = "Verdana"
        admin_unit.widget_background_color = Color("#eceef0")
        admin_unit.widget_primary_color = Color("#b09641")
        admin_unit.widget_link_color = Color("#7b2424")
        db.session.commit()

    url = utils.get_url("widget_event_dates", id=admin_unit_id)
    utils.get_ok(url)
