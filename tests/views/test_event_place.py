import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    response = utils.get_ok(url)

    # Validation
    utils.ajax_validation(url, "name", "Meine Crew 2", True)
    utils.ajax_validation(url, "name", "Meine Crew", False)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Ort",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = (
            EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
            .filter(EventPlace.name == "Neuer Ort")
            .first()
        )
        assert place is not None


@pytest.mark.parametrize("db_error", [True, False])
def test_update(client, seeder, utils, app, db, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "name": "Neuer Name",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Neuer Name"


def test_update_otherAdminUnit(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_default_event_place(admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=other_admin_unit_id,
        event_place_id=place_id,
    )
    utils.get_unauthorized(url)


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base()
    place_id = seeder.upsert_event_place(admin_unit_id, "Mein Ort")

    url = utils.get_url(
        "manage_admin_unit.event_place_delete",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Mein Ort"

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
            response, "Der eingegebene Name entspricht nicht dem Namen des Ortes"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place is None


def test_create_Unauthorized(client, app, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.event_place_create", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "manage_admin_unit", id=admin_unit_id
    )


def test_create_admin(client, app, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    utils.get_ok(url)
