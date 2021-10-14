from tests.seeder import Seeder
from tests.utils import UtilActions


def test_js_check_org_short_name(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_short_name")
        response = utils.post_form_data(
            url,
            {
                "short_name": "meinecrew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json


def test_js_check_org_short_name_exists(client, seeder, utils):
    seeder.create_user(admin=True)
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_short_name")
        response = utils.post_form_data(
            url,
            {
                "short_name": "meinecrew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json == "Der Kurzname ist bereits vergeben"


def test_js_check_org_name(client, seeder, utils):
    seeder.create_user(admin=True)
    utils.login()

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_name")
        response = utils.post_form_data(
            url,
            {
                "name": "Meine Crew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json


def test_js_check_org_name_exists(client, seeder, utils):
    seeder.create_user(admin=True)
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("admin_unit_create")
    response = utils.get(url)

    with client:
        url = utils.get_url("js_check_org_name")
        response = utils.post_form_data(
            url,
            {
                "name": "Meine Crew",
            },
        )
        utils.assert_response_ok(response)
        assert response.json == "Der Name ist bereits vergeben"


def test_js_js_check_register_email(client, seeder, utils):
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
        assert response.json


def test_js_js_check_register_email_exists(client, seeder, utils):
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
        assert response.json == "Mit dieser E-Mail existiert bereits ein Account."


def test_js_autocomplete_place(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
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

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
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


def test_js_autocomplete_gmaps_place(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("event_create_for_admin_unit_id", id=admin_unit_id)
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
