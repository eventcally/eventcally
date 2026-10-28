from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


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
        from project.infrastructure.models import EventReference

        reference = db.session.get(EventReference, reference_id)
        assert reference is None


# Organization-scoped routes


def _create_outgoing_reference(seeder: Seeder, admin_unit_id):
    """A reference of another organization to an event of `admin_unit_id`."""
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    event_id = seeder.create_event(admin_unit_id)
    reference_id = seeder.create_reference(event_id, other_admin_unit_id)
    return other_admin_unit_id, event_id, reference_id


def test_organization_incoming_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    response = utils.get_json_ok(url)
    assert response.json["id"] == reference_id


def test_organization_incoming_read_wrongSide(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, reference_id = _create_outgoing_reference(seeder, admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_incoming_read_otherOrganization(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_user_id = seeder.create_user("third@test.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    _, _, _, reference_id = seeder.create_any_reference(third_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.assert_response_notFound(utils.get_json(url))

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference",
        id=third_admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.assert_response_unauthorized(utils.get_json(url))


def test_organization_incoming_delete(client, app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.assert_response_no_content(utils.delete(url))

    with app.app_context():
        from project.infrastructure.models import EventReference

        assert db.session.get(EventReference, reference_id) is None


def test_organization_outgoing_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, reference_id = _create_outgoing_reference(seeder, admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    response = utils.get_json_ok(url)
    assert response.json["id"] == reference_id


def test_organization_outgoing_read_wrongSide(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_id = seeder.create_any_reference(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference",
        id=admin_unit_id,
        event_reference_id=reference_id,
    )
    utils.assert_response_notFound(utils.get_json(url))
