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
def test_update(client, seeder: Seeder, utils: UtilActions, app, db, mocker, db_error):
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


@pytest.mark.parametrize("change_location", [True, False])
def test_update_location(
    client, seeder: Seeder, utils: UtilActions, app, db, change_location
):
    _, admin_unit_id = seeder.setup_base()

    from project.models import Location

    place_id = seeder.upsert_event_place(
        admin_unit_id,
        "Place",
        Location(
            street="Markt 7",
            postalCode="38640",
            city="Goslar",
            latitude=51.9077888,
            longitude=10.4333312,
        ),
    )

    url = utils.get_url(
        "manage_admin_unit.event_place_update",
        id=admin_unit_id,
        event_place_id=place_id,
    )
    response = utils.get_ok(url)

    # 1. Update location
    data = dict()
    response = utils.post_form(
        url,
        response,
        data,
    )
    app.test_event_dispatcher.events.clear()

    # 2. Update location
    response = utils.get_ok(url)

    if change_location:
        data = {
            "location-street": "Neue Straße 1",
        }
    response = utils.post_form(
        url,
        response,
        data,
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.event_places", id=admin_unit_id
    )

    with app.app_context():
        from project.domain.events.event_place_updated import EventPlaceUpdated

        event_place_updated = app.test_event_dispatcher.get_first_event_by_type(
            EventPlaceUpdated
        )

        if change_location:
            assert event_place_updated.model_fields_set == {
                "actor",
                "id",
                "admin_unit_id",
                "location",
            }
            assert event_place_updated.location.new.street == "Neue Straße 1"
        else:
            assert event_place_updated is None


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
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_create_admin(client, app, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    url = utils.get_url("manage_admin_unit.event_place_create", id=admin_unit_id)
    utils.get_ok(url)
