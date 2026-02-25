from tests.seeder import Seeder
from tests.utils import UtilActions


def test_organizers(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organization_organizer_list", id=admin_unit_id)
    utils.get_json_ok(url)

    url = utils.get_url(
        "api_v1_organization_organizer_list", id=admin_unit_id, name="crew"
    )
    utils.get_json_ok(url)


def test_organizers_post(client, seeder: Seeder, utils: UtilActions, app):
    try:
        app.container.cqrs.event_dispatcher.reset_override()
        user_id, admin_unit_id = seeder.setup_api_access()

        url = utils.get_url("api_v1_organization_organizer_list", id=admin_unit_id)
        response = utils.post_json(
            url,
            {
                "name": "Neuer Organisator",
                "url": "http://test.de",
                "email": "test@example.com",
                "phone": "1234567890",
                "fax": "0987654321",
                "location": {
                    "street": "Straße 1",
                    "postalCode": "38640",
                    "city": "Goslar",
                    "latitude": "51.9077888",
                    "longitude": "10.4333312",
                },
            },
        )
        utils.assert_response_created(response)
        assert "id" in response.json
    finally:
        app.container.cqrs.event_dispatcher.override(app.test_event_dispatcher)

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


def test_put_location(client, seeder: Seeder, utils: UtilActions, app, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    organizer_id = seeder.upsert_default_event_organizer(admin_unit_id)

    url = utils.get_url("api_v1_organizer", id=organizer_id)
    response = utils.put_json(
        url, {"name": "Neuer Name", "location": {"postalCode": "54321"}}
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventOrganizer

        organizer = db.session.get(EventOrganizer, organizer_id)
        assert organizer.name == "Neuer Name"
        assert organizer.location.postalCode == "54321"


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
