from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_js_js_check_register_email(client, seeder: Seeder, utils: UtilActions):
    url = utils.get_url("security.register")
    response = utils.get(url)

    with client:
        url = utils.get_url("main.js_check_register_email")
        response = utils.post_form_data(
            url,
            {
                "email": "test@test.de",
            },
        )
        utils.assert_response_ok(response)
        assert response.json is True


def test_js_js_check_register_email_exists(client, seeder: Seeder, utils: UtilActions):
    seeder.create_user()
    url = utils.get_url("security.register")
    response = utils.get(url)

    url = utils.get_url("main.js_check_register_email")
    response = utils.get(url)

    with client:
        url = utils.get_url("main.js_check_register_email")
        response = utils.post_form_data(
            url,
            {
                "email": "test@test.de",
            },
        )
        utils.assert_response_ok(response)
        assert (
            response.json
            == 'Mit dieser E-Mail existiert bereits ein Account. &ndash; <a href="/reset">Passwort vergessen?</a>'
        )


def test_js_widget_loader_custom_widget(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("main.js_widget_loader_custom_widget", id=custom_widget_id)
    response = utils.get_ok(url)

    # The shape is a wire contract: the widget loader on customer sites reads it.
    body = response.json
    assert set(body) == {
        "id",
        "widget_type",
        "name",
        "settings",
        "created_at",
        "updated_at",
        "organization",
    }
    assert body["id"] == custom_widget_id
    assert body["widget_type"] == "search"
    assert body["name"] == "Mein Widget"
    assert body["settings"] == {"color": "black"}
    assert body["created_at"].endswith("+00:00")
    assert body["updated_at"] is None
    assert body["organization"] == {"id": admin_unit_id, "name": "Meine Crew"}


def test_js_widget_loader_custom_widget_not_found(
    client, seeder: Seeder, utils: UtilActions
):
    url = utils.get_url("main.js_widget_loader_custom_widget", id=4711)
    utils.assert_response_notFound(utils.get(url))


def test_gmt_iso_handles_naive_and_aware_datetimes():
    from datetime import datetime, timedelta, timezone

    from project.presentation.web.views.js import _gmt_iso

    assert _gmt_iso(None) is None
    assert _gmt_iso(datetime(2026, 1, 1, 10, 0)) == "2026-01-01T10:00:00+00:00"
    aware = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=2)))
    assert _gmt_iso(aware) == "2026-01-01T10:00:00+00:00"
