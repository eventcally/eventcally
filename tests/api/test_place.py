from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    utils.get_json_ok(url)


def test_put(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    url = utils.get_url("api_v1_place", id=place_id)
    response = utils.put_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Neuer Name"


def test_put_nonActiveReturnsUnauthorized(client, seeder, db, utils, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from project.models import User

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
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place.name == "Meine Crew"
        assert place.description == "Klasse"


def test_patch_location(db, seeder: Seeder, utils: UtilActions, app):
    user_id, admin_unit_id = seeder.setup_api_access()
    place_id = seeder.upsert_default_event_place(admin_unit_id)

    with app.app_context():
        from project.models import EventPlace, Location

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
        from project.models import EventPlace

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
        from project.models import EventPlace

        place = db.session.get(EventPlace, place_id)
        assert place is None
