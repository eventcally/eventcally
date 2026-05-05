import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get_ok(url)

    # Validation
    utils.ajax_validation(url, "name", "Meine Crew 2", True)
    utils.ajax_validation(url, "name", "Meine Crew", False)

    # Google Place Autocomplete
    utils.ajax_google_places(url, "location-google_place", "test")
    utils.ajax_google_place(url, "location-google_place", "123")

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Organisator",
            "url": "http://test.de",
            "email": "test@example.com",
            "phone": "1234567890",
            "fax": "0987654321",
            "location-street": "Straße 1",
            "location-postalCode": "38640",
            "location-city": "Goslar",
            "location-latitude": "51.9077888",
            "location-longitude": "10.4333312",
            "logo-image_base64": seeder.get_default_image_upload_base64(),
            "logo-copyright_text": "EventCally",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventOrganizer

        organizer = (
            EventOrganizer.query.filter(EventOrganizer.admin_unit_id == admin_unit_id)
            .filter(EventOrganizer.name == "Neuer Organisator")
            .first()
        )
        assert organizer is not None
        assert organizer.name == "Neuer Organisator"
        assert organizer.url == "http://test.de"
        assert organizer.email == "test@example.com"
        assert organizer.phone == "1234567890"
        assert organizer.fax == "0987654321"
        location = organizer.location
        assert location.street == "Straße 1"
        assert location.postalCode == "38640"
        assert location.city == "Goslar"
        assert float(location.latitude) == float("51.9077888")
        assert float(location.longitude) == float("10.4333312")
        assert organizer.logo is not None
        assert organizer.logo.copyright_text == "EventCally"


def test_create_logo_too_small(client, app, utils, seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.event_organizer_create", id=admin_unit_id)
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Organisator",
            "logo-image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
        },
    )

    utils.assert_response_error_message(response)


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Name",
            "logo-delete_flag": "y",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer.name == "Neuer Name"


def test_update_logo(client, seeder, utils, app, db, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_organizer_update",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "logo-image_base64": seeder.get_default_image_upload_base64(),
            "logo-copyright_text": "New EventCally",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer.logo is not None
        assert organizer.logo.copyright_text == "New EventCally"


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base()
    organizer_id = seeder.upsert_event_organizer(admin_unit_id, "Mein Organisator")

    url = utils.get_url(
        "manage_admin_unit.event_organizer_delete",
        id=admin_unit_id,
        event_organizer_id=organizer_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Mein Organisator"

    if non_match:
        form_name = "Falscher Name"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response,
            "Der eingegebene Name entspricht nicht dem Namen des Veranstalters",
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_organizers", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer is None


def test_organizers(client, seeder, utils):
    url = utils.get_url("main.organizers")
    utils.get_ok(url)


def test_ical(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)

    seeder.create_event(admin_unit_id, end=seeder.get_now_by_minute())
    url = utils.get_url("main.organizer_ical", id=admin_unit_id)
    utils.get_ok(url)
