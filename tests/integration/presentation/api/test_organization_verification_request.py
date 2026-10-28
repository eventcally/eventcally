from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


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
        from project.infrastructure.models import EventReferenceRequest

        reference = db.session.get(EventReferenceRequest, reference_request_id)
        assert reference is None


def test_verify(client, app, db, seeder: Seeder, utils: UtilActions, mocker):
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

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "mitglied@verein.de"

    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest
        from project.infrastructure.seed_helpers import get_admin_unit_relation

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


def test_verify_outside_allowed_postal_codes(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(
        log_in_verifier=True, api=True
    )
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(
            AdminUnit, verifier_admin_unit_id
        ).incoming_verification_requests_postal_codes = ["99999"]
        db.session.commit()

    url = utils.get_url(
        "api_v1_organization_verification_request_verify", id=request_id
    )
    response = utils.post_json(url, {})
    utils.assert_response_created(response)


def test_verify_withoutBody(client, app, db, seeder: Seeder, utils: UtilActions):
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
    response = client.post(url, headers=utils.get_headers())
    utils.assert_response_created(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest
        from project.infrastructure.seed_helpers import get_admin_unit_relation

        verification_request = db.session.get(
            AdminUnitVerificationRequest, reference_request_id
        )
        assert verification_request.verified

        relation = get_admin_unit_relation(
            verifier_admin_unit_id, unverified_admin_unit_id
        )
        assert relation is not None
        assert relation.verify
        assert not relation.auto_verify_event_reference_requests


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
        from project.infrastructure.models import (
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

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert len(app.test_email_service.sent_emails) == 1
    assert app.test_email_service.sent_emails[0]["recipient"] == "mitglied@verein.de"

    with app.app_context():
        from project.infrastructure.models import (
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


# Organization-scoped routes


def _scenario(seeder: Seeder, log_in_verifier: bool):
    (
        verifier_user_id,
        verifier_admin_unit_id,
        unverified_user_id,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(
        log_in_verifier=log_in_verifier, api=True
    )
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    return verifier_admin_unit_id, unverified_admin_unit_id, request_id


def test_organization_outgoing_read(client, seeder: Seeder, utils: UtilActions):
    _, source_id, request_id = _scenario(seeder, False)

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request",
        id=source_id,
        organization_verification_request_id=request_id,
    )
    assert utils.get_json_ok(url).json["id"] == request_id


def test_organization_outgoing_read_wrongSide(client, seeder: Seeder, utils):
    target_id, _, request_id = _scenario(seeder, True)

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request",
        id=target_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_outgoing_read_otherOrganization(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_user_id = seeder.create_user("third@test.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    _, _, request_id = seeder.create_incoming_admin_unit_verification_request(
        third_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request",
        id=admin_unit_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_outgoing_delete(client, app, db, seeder: Seeder, utils):
    _, source_id, request_id = _scenario(seeder, False)

    url = utils.get_url(
        "api_v1_organization_outgoing_organization_verification_request",
        id=source_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_no_content(utils.delete(url))

    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest

        assert db.session.get(AdminUnitVerificationRequest, request_id) is None


def test_organization_incoming_read(client, seeder: Seeder, utils: UtilActions):
    target_id, _, request_id = _scenario(seeder, True)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request",
        id=target_id,
        organization_verification_request_id=request_id,
    )
    assert utils.get_json_ok(url).json["id"] == request_id


def test_organization_incoming_read_wrongSide(client, seeder: Seeder, utils):
    _, source_id, request_id = _scenario(seeder, False)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request",
        id=source_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_incoming_verify(client, app, db, seeder: Seeder, utils):
    target_id, source_id, request_id = _scenario(seeder, True)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request_verify",
        id=target_id,
        organization_verification_request_id=request_id,
    )
    response = utils.post_json(url, {"auto_verify_event_reference_requests": True})
    utils.assert_response_created(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitVerificationRequest
        from project.infrastructure.seed_helpers import get_admin_unit_relation

        assert db.session.get(AdminUnitVerificationRequest, request_id).verified
        relation = get_admin_unit_relation(target_id, source_id)
        assert relation.id == int(response.json["id"])
        assert relation.auto_verify_event_reference_requests

    # Verified requests cannot be verified or rejected again.
    utils.assert_response_unprocessable_entity(utils.post_json(url, {}))
    reject_url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request_reject",
        id=target_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_unprocessable_entity(
        utils.post_json(reject_url, {"rejection_reason": "unknown"})
    )


def test_organization_incoming_verify_wrongSide(client, seeder: Seeder, utils):
    _, source_id, request_id = _scenario(seeder, False)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request_verify",
        id=source_id,
        organization_verification_request_id=request_id,
    )
    utils.assert_response_notFound(utils.post_json(url, {}))


def test_organization_incoming_reject(client, app, db, seeder: Seeder, utils):
    target_id, _, request_id = _scenario(seeder, True)

    url = utils.get_url(
        "api_v1_organization_incoming_organization_verification_request_reject",
        id=target_id,
        organization_verification_request_id=request_id,
    )
    response = utils.post_json(url, {"rejection_reason": "unknown"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        assert (
            db.session.get(AdminUnitVerificationRequest, request_id).review_status
            == AdminUnitVerificationRequestReviewStatus.rejected
        )
