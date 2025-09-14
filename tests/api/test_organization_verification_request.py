from tests.seeder import Seeder
from tests.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(api=True)
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url("api_v1_organization_verification_request", id=request_id)
    utils.get_json_ok(url)


def test_read_noAccess(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_user_id = seeder.create_user("third@test.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        request_id,
    ) = seeder.create_incoming_admin_unit_verification_request(third_admin_unit_id)

    url = utils.get_url("api_v1_organization_verification_request", id=request_id)
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


def test_delete(client, app, db, seeder: Seeder, utils: UtilActions):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(api=True)
    reference_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_verification_request", id=reference_request_id
    )
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import EventReferenceRequest

        reference = db.session.get(EventReferenceRequest, reference_request_id)
        assert reference is None


def test_verify(client, app, db, seeder: Seeder, utils: UtilActions, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(
        log_in_verifier=True, api=True
    )
    reference_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_verification_request_verify", id=reference_request_id
    )
    data = {
        "auto_verify_event_reference_requests": True,
    }
    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json
    utils.assert_send_mail_called(mail_mock, "mitglied@verein.de")

    with app.app_context():
        from project.models import AdminUnitVerificationRequest
        from project.services.admin_unit import get_admin_unit_relation

        verification_request = db.session.get(
            AdminUnitVerificationRequest, reference_request_id
        )
        assert verification_request.verified

        relation = get_admin_unit_relation(
            verifier_admin_unit_id, unverified_admin_unit_id
        )
        assert relation is not None
        assert relation.id == int(response.json["id"])
        assert relation.verify
        assert relation.auto_verify_event_reference_requests


def test_verify_alreadyVerified(
    client, app, db, seeder: Seeder, utils: UtilActions, mocker
):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(
        log_in_verifier=True, api=True
    )
    reference_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        verification_request = db.session.get(
            AdminUnitVerificationRequest, reference_request_id
        )

        verification_request.review_status = (
            AdminUnitVerificationRequestReviewStatus.verified
        )
        db.session.commit()

    url = utils.get_url(
        "api_v1_organization_verification_request_verify", id=reference_request_id
    )
    data = {
        "auto_verify_event_reference_requests": True,
    }
    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)


def test_reject(client, app, db, seeder: Seeder, utils: UtilActions, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(
        log_in_verifier=True, api=True
    )
    reference_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_verification_request_reject", id=reference_request_id
    )
    data = {
        "rejection_reason": "unknown",
    }
    response = utils.post_json(url, data)
    utils.assert_response_no_content(response)
    utils.assert_send_mail_called(mail_mock, "mitglied@verein.de")

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestRejectionReason,
            AdminUnitVerificationRequestReviewStatus,
        )

        verification_request = db.session.get(
            AdminUnitVerificationRequest, reference_request_id
        )
        assert (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.rejected
        )
        assert (
            verification_request.rejection_reason
            == AdminUnitVerificationRequestRejectionReason.unknown
        )
