import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_admin_unit_verification_requests_incoming(
    client, utils: UtilActions, seeder: Seeder
):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_incoming_admin_unit_verification_request(admin_unit_id)

    # The list is a Vue page; it reads the filter from the query string.
    response = utils.get_endpoint_ok(
        "manage_admin_unit.incoming_organization_verification_requests",
        id=admin_unit_id,
        review_status=1,
    )
    assert b'id="app"' in response.data


def test_incoming_list_requires_permission(client, seeder, utils: UtilActions):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.incoming_organization_verification_requests",
        id=admin_unit_id,
    )
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_verification_requests_outgoing(client, seeder: Seeder, utils: UtilActions):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()

    # No redirect to a selection any more: the Vue list opens the request dialog.
    response = utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_organization_verification_requests",
        id=unverified_admin_unit_id,
    )
    assert b'id="app"' in response.data

    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    response = utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_organization_verification_request",
        id=unverified_admin_unit_id,
        organization_verification_request_id=request_id,
    )
    assert b'id="app"' in response.data


def test_read_of_another_organization_is_unauthorized(
    client, seeder: Seeder, utils: UtilActions
):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    second_admin_unit_id = seeder.create_admin_unit(
        unverified_user_id, "Zweite Crew", verified=True
    )

    response = utils.get(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_verification_request",
            id=second_admin_unit_id,
            organization_verification_request_id=request_id,
        )
    )

    utils.assert_response_unauthorized(response)


@pytest.mark.parametrize(
    "path",
    [
        "admin_unit/{id}/outgoing_organization_verification_request/{rid}/delete",
        "admin_unit/{id}/verification_requests/outgoing/create/select",
        "admin_unit/{id}/verification_requests/outgoing/create/target/{rid}",
    ],
)
def test_removed_pages_are_gone(client, seeder: Seeder, utils: UtilActions, path):
    # Withdrawing and requesting are modals of the Vue pages (`/bff/manage`).
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    response = utils.get(
        "/manage/" + path.format(id=unverified_admin_unit_id, rid=request_id)
    )

    utils.assert_response_notFound(response)
