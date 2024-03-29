from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access(user_access=False)
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("api_v1_event_reference", id=reference_id)
    utils.get_json_ok(url)


def test_delete(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_id,
    ) = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url("api_v1_event_reference", id=reference_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventReference

        reference = db.session.get(EventReference, reference_id)
        assert reference is None
