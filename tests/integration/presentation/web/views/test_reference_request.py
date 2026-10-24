from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create(client, app, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request_create_for_event",
        id=admin_unit_id,
        event_id=event_id,
    )

    # The page is a Vue 3 shell, the form reads and saves through the BFF.
    response = utils.get_ok(url)
    assert b'id="app"' in response.data


def test_create_unverifiedAdminUnitNotAllowed(
    client, app, utils: UtilActions, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url(
        "manage_admin_unit.outgoing_event_reference_request_create_for_event",
        id=admin_unit_id,
        event_id=event_id,
    )
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_create_unknownEvent(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request_create_for_event",
            id=admin_unit_id,
            event_id=4711,
        )
    )
    utils.assert_response_notFound(response)


def test_admin_unit_reference_requests_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_incoming_reference_request(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.incoming_event_reference_requests", id=admin_unit_id
    )


def test_admin_unit_reference_requests_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_outgoing_reference_request(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_event_reference_requests", id=admin_unit_id
    )
