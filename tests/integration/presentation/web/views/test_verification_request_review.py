from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _review_url(utils, admin_unit_id, request_id):
    return utils.get_url(
        "manage_admin_unit.incoming_organization_verification_request_review",
        id=admin_unit_id,
        organization_verification_request_id=request_id,
    )


def test_review_renders_the_shell(client, seeder: Seeder, utils: UtilActions):
    (
        _,
        verifier_admin_unit_id,
        _,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )
    url = _review_url(utils, verifier_admin_unit_id, request_id)

    legacy_review_url = utils.get_url(
        "main.manage_admin_unit_incoming_admin_unit_verification_request_review",
        id=verifier_admin_unit_id,
        admin_unit_verification_request_id=request_id,
    )
    utils.assert_response_redirect_to_url(client.get(legacy_review_url), url)

    response = utils.get_ok(url)

    assert b'<div id="app"' in response.data
    assert "Verifizierungsanfrage prüfen".encode() in response.data


def test_review_of_a_verified_request_redirects_to_the_list(
    client, seeder: Seeder, utils: UtilActions, app, db
):
    (
        _,
        verifier_admin_unit_id,
        _,
        unverified_admin_unit_id,
    ) = seeder.setup_admin_unit_missing_verification_scenario(log_in_verifier=True)
    request_id = seeder.create_admin_unit_verification_request(
        unverified_admin_unit_id, verifier_admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import (
            AdminUnitVerificationRequest,
            AdminUnitVerificationRequestReviewStatus,
        )

        verification_request = db.session.get(AdminUnitVerificationRequest, request_id)
        verification_request.review_status = (
            AdminUnitVerificationRequestReviewStatus.verified
        )
        db.session.commit()

    response = client.get(_review_url(utils, verifier_admin_unit_id, request_id))

    utils.assert_response_redirect(
        response,
        "manage_admin_unit.incoming_organization_verification_requests",
        id=verifier_admin_unit_id,
    )
    with client.session_transaction() as session:
        categories = [category for category, _ in session["_flashes"]]
    assert categories == ["danger"]


def test_review_status_unauthorized_redirects_to_login(
    client, seeder: Seeder, utils: UtilActions
):
    seeder.create_user()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        verification_request_id,
    ) = seeder.create_incoming_admin_unit_verification_request(third_admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_verification_request",
        id=other_admin_unit_id,
        organization_verification_request_id=verification_request_id,
    )

    legacy_review_url = utils.get_url(
        "main.manage_admin_unit_outgoing_admin_unit_verification_request",
        id=other_admin_unit_id,
        admin_unit_verification_request_id=verification_request_id,
    )
    utils.assert_response_redirect_to_url(client.get(legacy_review_url), url)

    response = client.get(url)
    utils.assert_response_redirect_to_login(response, url)
