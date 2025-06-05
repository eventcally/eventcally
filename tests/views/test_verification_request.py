import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, db_error):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()

    url = utils.get_url(
        "manage_organization_requests_outgoing_create",
        id=unverified_admin_unit_id,
        target_id=verifier_admin_unit_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    mail_mock = utils.mock_send_mails_async(mocker)
    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response,
        "manage_admin_unit.outgoing_organization_verification_requests",
        id=unverified_admin_unit_id,
    )
    utils.assert_send_mail_called(mail_mock, "test@test.de")

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        verification_request = (
            AdminUnitVerificationRequest.query.filter(
                AdminUnitVerificationRequest.source_admin_unit_id
                == unverified_admin_unit_id
            )
            .filter(
                AdminUnitVerificationRequest.target_admin_unit_id
                == verifier_admin_unit_id
            )
            .first()
        )
        assert verification_request is not None
        assert (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.inbox
        )


def test_admin_unit_verification_requests_incoming(
    client, utils: UtilActions, seeder: Seeder
):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_incoming_admin_unit_verification_request(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit.incoming_organization_verification_requests",
        id=admin_unit_id,
        review_status=-1,
    )
    utils.get_endpoint_ok(
        "manage_admin_unit.incoming_organization_verification_requests",
        id=admin_unit_id,
        review_status=1,
    )


def test_verification_requests_outgoing(client, seeder: Seeder, utils: UtilActions):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()

    response = utils.get_endpoint(
        "manage_admin_unit.outgoing_organization_verification_requests",
        id=unverified_admin_unit_id,
    )
    utils.assert_response_redirect(
        response,
        "manage_organization_verification_requests_outgoing_create_select",
        id=unverified_admin_unit_id,
    )

    response = utils.get_endpoint_ok(
        "manage_organization_verification_requests_outgoing_create_select",
        id=unverified_admin_unit_id,
    )
    utils.assert_response_contains(response, "Stadtmarketing")
    utils.assert_response_contains(response, "Please give us a call")

    seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    response = utils.get_endpoint_ok(
        "manage_admin_unit.outgoing_organization_verification_requests",
        id=unverified_admin_unit_id,
    )


@pytest.mark.parametrize("db_error", [True, False])
def test_delete(client, seeder: Seeder, utils: UtilActions, app, db, mocker, db_error):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario()
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_verification_request_delete",
        id=unverified_admin_unit_id,
        organization_verification_request_id=request_id,
    )
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response,
        "manage_admin_unit.outgoing_organization_verification_requests",
        id=unverified_admin_unit_id,
    )

    with app.app_context():
        from project.models import AdminUnitVerificationRequest

        request = db.session.get(AdminUnitVerificationRequest, request_id)
        assert request is None
