import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_places(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id, name="crew")
    utils.get_json_ok(url)


@pytest.mark.parametrize("as_app_installation", [True, False])
def test_places_post(
    client, seeder: Seeder, utils: UtilActions, app, as_app_installation: bool
):
    user_id, admin_unit_id = seeder.setup_api_access(
        as_app_installation=as_app_installation
    )

    url = utils.get_url("api_v1_organization_place_list", id=admin_unit_id)
    response = utils.post_json(
        url,
        {
            "name": "Neuer Ort",
            "location": {"street": "Straße 1", "postalCode": "38640", "city": "Goslar"},
        },
    )
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = (
            EventPlace.query.filter(EventPlace.admin_unit_id == admin_unit_id)
            .filter(EventPlace.name == "Neuer Ort")
            .first()
        )
        assert place is not None
        assert place.name == "Neuer Ort"
        assert place.location.street == "Straße 1"
        assert place.location.postalCode == "38640"
        assert place.location.city == "Goslar"
        assert place.created_by_label is not None

        if as_app_installation:
            assert place.created_by_app_installation_id is not None
        else:
            assert place.created_by is not None

    # Test duplicate name
    response = utils.post_json(
        url,
        {"name": "Neuer Ort"},
    )
    utils.assert_response_bad_request(response)


def test_read(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    utils.get_json_ok(url)


@pytest.mark.parametrize("as_app_installation", [True, False])
def test_put(
    client, seeder: Seeder, utils: UtilActions, app, db, as_app_installation: bool
):
    user_id, admin_unit_id = seeder.setup_api_access(
        as_app_installation=as_app_installation
    )
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.put_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Neuer Name"
        assert place.updated_by_label is not None

        if as_app_installation:
            assert place.updated_by_app_installation_id is not None
        else:
            assert place.updated_by is not None


def test_put_nonActiveReturnsUnauthorized(client, seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import User

        user = db.session.get(User, user_id)
        user.active = False
        db.session.commit()

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.put_json(url, {"name": "Neuer Name"})
    utils.assert_response_unauthorized(response)


def test_patch(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.patch_json(url, {"description": "Klasse"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Meine Crew"
        assert place.description == "Klasse"


def test_patch_location(db, seeder: Seeder, utils: UtilActions, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import EventPlace, Location

        location = Location()
        location.postalCode = "12345"
        location.city = "City"

        event = db.session.get(EventPlace, place_id)
        event.location = location
        db.session.commit()

        location_id = location.id

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.patch_json(
        url,
        {"location": {"postalCode": "54321"}},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.location.id == location_id
        assert place.location.postalCode == "54321"


def test_delete(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place is None


# Organization-scoped routes


def _org_url(utils, admin_unit_id, place_id):
    return utils.get_url(
        "api_v1_organization_place", id=admin_unit_id, place_id=place_id
    )


def _other_organization(seeder: Seeder):
    other_user_id = seeder.create_user("other@test.de")
    return seeder.create_admin_unit(other_user_id, "Other Crew")


def test_organization_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    response = utils.get_json_ok(_org_url(utils, admin_unit_id, place_id))
    assert response.json["id"] == place_id


def test_organization_read_anonym(client, app, seeder: Seeder, utils: UtilActions):
    app.config["API_READ_ANONYM"] = True
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    utils.get_json_ok(_org_url(utils, admin_unit_id, place_id))


def test_organization_read_otherOrganization(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = _other_organization(seeder)
    place_id = seeder.upsert_default_event_place(other_admin_unit_id)

    utils.assert_response_notFound(
        utils.get_json(_org_url(utils, admin_unit_id, place_id))
    )
    utils.get_json_ok(_org_url(utils, other_admin_unit_id, place_id))
    utils.assert_response_notFound(utils.get_json(_org_url(utils, admin_unit_id, 4711)))


def test_organization_put(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    response = utils.put_json(
        _org_url(utils, admin_unit_id, place_id), {"name": "Neuer Name"}
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        assert db.session.get(EventPlace, place_id).name == "Neuer Name"


def test_organization_patch(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    response = utils.patch_json(
        _org_url(utils, admin_unit_id, place_id), {"description": "Klasse"}
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        assert db.session.get(EventPlace, place_id).description == "Klasse"


def test_organization_delete(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    response = utils.delete(_org_url(utils, admin_unit_id, place_id))
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventPlace

        assert db.session.get(EventPlace, place_id) is None


def test_organization_write_otherOrganization(
    client, seeder: Seeder, utils: UtilActions, app, db
):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_admin_unit_id = _other_organization(seeder)
    place_id = seeder.upsert_default_event_place(other_admin_unit_id)

    # The place belongs to another organization than the path names: 404.
    url = _org_url(utils, admin_unit_id, place_id)
    utils.assert_response_notFound(utils.put_json(url, {"name": "Neu"}))
    utils.assert_response_notFound(utils.patch_json(url, {"name": "Neu"}))
    utils.assert_response_notFound(utils.delete(url))

    # An outsider of the organization named in the path: 401.
    url = _org_url(utils, other_admin_unit_id, place_id)
    utils.assert_response_unauthorized(utils.put_json(url, {"name": "Neu"}))
    utils.assert_response_unauthorized(utils.delete(url))

    with app.app_context():
        from project.infrastructure.models import EventPlace

        assert db.session.get(EventPlace, place_id) is not None
