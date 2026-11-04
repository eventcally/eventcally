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


def test_admin_unit_reference_requests_are_shells(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_outgoing_reference_request(admin_unit_id)

    for endpoint in (
        "manage_admin_unit.incoming_event_reference_requests",
        "manage_admin_unit.outgoing_event_reference_requests",
    ):
        response = utils.get_endpoint_ok(endpoint, id=admin_unit_id)
        assert b'id="app"' in response.data


def test_outgoing_read_is_a_shell(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    _, _, _, request_id = seeder.create_outgoing_reference_request(admin_unit_id)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request",
            id=admin_unit_id,
            event_reference_request_id=request_id,
        )
    )

    assert b'id="app"' in response.data


def test_outgoing_read_of_another_organization_is_401(seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    _, _, _, request_id = seeder.create_outgoing_reference_request(admin_unit_id)
    second_admin_unit_id = seeder.create_admin_unit(user_id, "Zweite Crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request",
            id=second_admin_unit_id,
            event_reference_request_id=request_id,
        )
    )


def test_outgoing_read_unknown_is_404(seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get(
        utils.get_url(
            "manage_admin_unit.outgoing_event_reference_request",
            id=admin_unit_id,
            event_reference_request_id=4711,
        )
    )

    utils.assert_response_notFound(response)
