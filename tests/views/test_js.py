from tests.seeder import Seeder
from tests.utils import UtilActions


def test_js_check_event_place_name(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_event_place_name")
        response = utils.post_form_data(
            url,
            {
                "admin_unit_id": admin_unit_id,
                "name": "Meine Crew 2",
            },
        )
        utils.assert_response_ok(response)
        assert response.json is True


def test_js_check_event_place_name_exists(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_event_place_name")
        response = utils.post_form_data(
            url,
            {
                "admin_unit_id": admin_unit_id,
                "name": "Meine Crew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json == "Mit diesem Namen existiert bereits ein Ort."


def test_js_check_organizer_name(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_organizer_name")
        response = utils.post_form_data(
            url,
            {
                "admin_unit_id": admin_unit_id,
                "name": "Meine Crew 2",
            },
        )
        utils.assert_response_ok(response)
        assert response.json is True


def test_js_check_organizer_name_exists(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_organizer_name")
        response = utils.post_form_data(
            url,
            {
                "admin_unit_id": admin_unit_id,
                "name": "Meine Crew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json == "Mit diesem Namen existiert bereits ein Veranstalter."


def test_js_js_check_register_email(client, seeder: Seeder, utils: UtilActions):
    url = utils.get_url("security.register")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_register_email")
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

    url = utils.get_url("js_check_register_email")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_register_email")
        response = utils.post_form_data(
            url,
            {
                "email": "test@test.de",
            },
        )
        utils.assert_response_ok(response)
        assert (
            response.json
            == 'Mit dieser E-Mail existiert bereits ein Account. &ndash; <a href="/reset">Passwort vergessen</a>'
        )


def test_js_autocomplete_place(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get(url)

    utils.gmaps_places_autocomplete_query.return_value = [
        {
            "place_id": "123",
            "description": "Beschreibung",
            "structured_formatting": {"main_text": "Haupttext"},
        }
    ]

    with client:
        url = utils.get_url(
            "js_autocomplete_place", admin_unit_id=admin_unit_id, keyword="crew"
        )
        response = utils.get(url)

        utils.assert_response_ok(response)
        assert response.json["results"][0]["children"][0]["text"] == "Meine Crew"
        assert response.json["results"][1]["children"][0]["text"] == "Beschreibung"


def test_js_autocomplete_place_gmaps_only(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_dates")
    response = utils.get(url)

    utils.gmaps_places_autocomplete_query.return_value = [
        {
            "place_id": "123",
            "description": "Beschreibung",
            "structured_formatting": {"main_text": "Haupttext"},
        }
    ]

    with client:
        url = utils.get_url("js_autocomplete_place", keyword="crew")
        response = utils.get(url)

        utils.assert_response_ok(response)
        assert response.json["results"][0]["text"] == "Beschreibung"


def test_js_autocomplete_place_exclude_gmaps(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get(url)

    with client:
        url = utils.get_url(
            "js_autocomplete_place",
            admin_unit_id=admin_unit_id,
            keyword="crew",
            exclude_gmaps=1,
        )
        response = utils.get(url)

        utils.assert_response_ok(response)
        assert response.json["results"][0]["text"] == "Meine Crew"

        utils.get_endpoint_ok(
            "js_autocomplete_place",
            admin_unit_id=admin_unit_id,
            exclude_gmaps=1,
        )


def test_js_autocomplete_gmaps_place(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_create", id=admin_unit_id)
    response = utils.get(url)

    utils.gmaps_place.return_value = {
        "status": "OK",
        "result": {
            "place_id": "123",
        },
    }

    with client:
        url = utils.get_url("js_autocomplete_gmaps_place", gmaps_id="123")
        response = utils.get(url)

        utils.assert_response_ok(response)
        assert response.json["place_id"] == "123"


def test_js_widget_loader_custom_widget(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    custom_widget_id = seeder.insert_event_custom_widget(admin_unit_id)

    url = utils.get_url("js_widget_loader_custom_widget", id=custom_widget_id)
    utils.get_ok(url)


def test_js_icalevents(
    client, app, db, seeder: Seeder, utils: UtilActions, shared_datadir, requests_mock
):
    user_id, admin_unit_id = seeder.setup_base()
    url = utils.get_url("planning")
    utils.get(url)

    with app.app_context():
        import json

        from project.services.admin import upsert_settings

        settings = upsert_settings()
        settings.planning_external_calendars = json.dumps(
            [
                {
                    "url": "http://test.de",
                }
            ]
        )
        db.session.commit()

    params = (client, utils, shared_datadir)
    _assert_icalevents(params, "feiertage-deutschland.ics")
    _assert_icalevents(params, "recurring-events-changed-duration.ics")


def _assert_icalevents(params, filename):
    client, utils, datadir = params

    utils.mock_get_request_with_file("http://test.de", datadir, filename)

    with client:
        url = utils.get_url("js_icalevents")
        response = utils.post_form_data(
            url,
            {
                "date_from": "2019-03-05",
                "date_to": "2019-04-01",
                "url": "http://test.de",
            },
        )
        utils.assert_response_ok(response)
        json = response.json
        first = json["items"][0]
        assert first["name"]
