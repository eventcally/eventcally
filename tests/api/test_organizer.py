from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organizer", id=organizer_id)
    utils.get_json_ok(url)


def test_put(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organizer", id=organizer_id)
    response = utils.put_json(url, {"name": "Neuer Name"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer.name == "Neuer Name"


def test_patch(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organizer", id=organizer_id)
    response = utils.patch_json(url, {"phone": "55555"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer.name == "Meine Crew"
        assert organizer.phone == "55555"


def test_delete(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organizer", id=organizer_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer is None
