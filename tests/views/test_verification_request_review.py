import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("is_verified", [True, False])
def test_review_verify(
    client, seeder: Seeder, utils: UtilActions, app, mocker, db, db_error, is_verified
):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    verification_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "admin_unit_verification_request_review", id=verification_request_id
    )

    if is_verified:
        with app.app_context():
            from project.models import (
                AdminUnitVerificationRequest,
                AdminUnitVerificationRequestReviewStatus,
            )

            verification_request = db.session.get(
                AdminUnitVerificationRequest, verification_request_id
            )
            verification_request.review_status = (
                AdminUnitVerificationRequestReviewStatus.verified
            )
            db.session.commit()

        response = client.get(url)
        utils.assert_response_redirect(
            response,
            "manage_admin_unit_verification_requests_incoming",
            id=verifier_admin_unit_id,
        )
        return

    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    mail_mock = utils.mock_send_mails_async(mocker)
    response = utils.post_form(
        url,
        response,
        {
            "review_status": 2,
            "auto_verify": 1,
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response,
        "manage_admin_unit_verification_requests_incoming",
        id=verifier_admin_unit_id,
    )
    utils.assert_send_mail_called(mail_mock, "mitglied@verein.de")

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )
        from project.services.admin_unit import get_admin_unit_relation

        verification_request = db.session.get(
            AdminUnitVerificationRequest, verification_request_id
        )
        assert verification_request.verified

        relation = get_admin_unit_relation(
            verifier_admin_unit_id, unverified_admin_unit_id
        )
        assert relation is not None
        assert relation.verify
        assert relation.auto_verify_event_reference_requests


def test_review_reject(client, seeder: Seeder, utils: UtilActions, app, db, mocker):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    verification_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "admin_unit_verification_request_review", id=verification_request_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "review_status": 3,
            "rejection_reason": 0,
        },
    )

    utils.assert_response_redirect(
        response,
        "manage_admin_unit_verification_requests_incoming",
        id=verifier_admin_unit_id,
    )

    with app.app_context():
        from project.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        verification_request = db.session.get(
            AdminUnitVerificationRequest, verification_request_id
        )
        assert (
            verification_request.review_status
            == AdminUnitVerificationRequestReviewStatus.rejected
        )
        assert verification_request.rejection_reason is None


def test_review_status(client, seeder: Seeder, utils: UtilActions):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    verification_request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    url = utils.get_url(
        "admin_unit_verification_request_review_status", id=verification_request_id
    )
    utils.get_ok(url)


def test_review_status_401_unauthorized(client, seeder: Seeder, utils: UtilActions):
    seeder.create_user()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        verification_request_id,
    ) = seeder.create_incoming_admin_unit_verification_request(third_admin_unit_id)

    url = utils.get_url(
        "admin_unit_verification_request_review_status", id=verification_request_id
    )
    response = client.get(url)
    assert response.status_code == 401
