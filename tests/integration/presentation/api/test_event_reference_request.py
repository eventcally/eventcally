from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_outgoing_reference_request(admin_unit_id)

    url = utils.get_url("api_v1_event_reference_request", id=reference_request_id)
    utils.get_json_ok(url)


def test_read_noAccess(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_user_id = seeder.create_user("third@test.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_outgoing_reference_request(third_admin_unit_id)

    url = utils.get_url("api_v1_event_reference_request", id=reference_request_id)
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


def test_delete(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_outgoing_reference_request(admin_unit_id)

    url = utils.get_url("api_v1_event_reference_request", id=reference_request_id)
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import EventReferenceRequest

        reference = db.session.get(EventReferenceRequest, reference_request_id)
        assert reference is None


def test_verify(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_reference_request_verify", id=reference_request_id
    )
    data = {
        "rating": 70,
    }
    response = utils.post_json(url, data)
    utils.assert_response_created(response)
    assert "id" in response.json

    with app.app_context():
        from project.infrastructure.models import (
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        )

        reference = db.session.get(EventReference, int(response.json["id"]))
        assert reference is not None
        assert reference.admin_unit_id == admin_unit_id
        assert reference.event_id == event_id
        assert reference.rating == 70


def test_reject(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_reference_request_reject", id=reference_request_id
    )
    data = {
        "rejection_reason": "duplicate",
    }
    response = utils.post_json(url, data)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestRejectionReason,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.rejected
        )
        assert (
            reference_request.rejection_reason
            == EventReferenceRequestRejectionReason.duplicate
        )


def test_reject_invalidRejectionReason(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_reference_request_reject", id=reference_request_id
    )
    data = {
        "rejection_reason": "bogus",
    }
    response = utils.post_json(url, data)
    utils.assert_response_unprocessable_entity(response)


def test_reject_nonJsonBody(client, app, db, seeder: Seeder, utils: UtilActions):
    """A non-JSON body is ignored rather than answered with 415.

    webargs parsed a body whose content type is not JSON as no payload at all,
    so clients sending a form-encoded body kept working. The command carries
    only optional fields, so it stays valid without them.
    """
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_reference_request_reject", id=reference_request_id
    )
    response = client.post(
        url,
        data="rejection_reason=duplicate",
        content_type="application/x-www-form-urlencoded",
        headers=utils.get_headers(),
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.rejected
        )
        assert reference_request.rejection_reason is None


def test_reject_withoutBody(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "api_v1_event_reference_request_reject", id=reference_request_id
    )
    response = client.post(url, headers=utils.get_headers())
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.rejected
        )
        assert reference_request.rejection_reason is None


# Organization-scoped routes


def _third_organization(seeder: Seeder):
    third_user_id = seeder.create_user("third@test.de")
    return seeder.create_admin_unit(third_user_id, "Third Crew")


def test_organization_outgoing_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_outgoing_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = utils.get_json_ok(url)
    assert response.json["id"] == reference_request_id


def test_organization_outgoing_read_otherOrganization(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_admin_unit_id = _third_organization(seeder)
    _, _, _, reference_request_id = seeder.create_outgoing_reference_request(
        third_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))

    # An outsider of the organization named in the path is unauthorized, not 404.
    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request",
        id=third_admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_unauthorized(utils.get_json(url))


def test_organization_outgoing_read_wrongSide(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_outgoing_delete(client, app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_outgoing_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_outgoing_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_no_content(utils.delete(url))

    with app.app_context():
        from project.infrastructure.models import EventReferenceRequest

        assert db.session.get(EventReferenceRequest, reference_request_id) is None


def test_organization_incoming_read(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = utils.get_json_ok(url)
    assert response.json["id"] == reference_request_id


def test_organization_incoming_read_wrongSide(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_outgoing_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_incoming_read_unknown(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request",
        id=admin_unit_id,
        event_reference_request_id=4711,
    )
    utils.assert_response_notFound(utils.get_json(url))


def test_organization_incoming_verify(client, app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, event_id, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request_verify",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = utils.post_json(url, {"rating": 70})
    utils.assert_response_created(response)

    with app.app_context():
        from project.infrastructure.models import EventReference

        reference = db.session.get(EventReference, int(response.json["id"]))
        assert reference.admin_unit_id == admin_unit_id
        assert reference.event_id == event_id
        assert reference.rating == 70


def test_organization_incoming_verify_wrongSide(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_outgoing_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request_verify",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_notFound(utils.post_json(url, {"rating": 70}))


def test_organization_incoming_reject(client, app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request_reject",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    response = utils.post_json(url, {"rejection_reason": "duplicate"})
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import (
            EventReferenceRequest,
            EventReferenceRequestRejectionReason,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.rejected
        )
        assert (
            reference_request.rejection_reason
            == EventReferenceRequestRejectionReason.duplicate
        )


def test_organization_incoming_reject_otherOrganization(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    third_admin_unit_id = _third_organization(seeder)
    _, _, _, reference_request_id = seeder.create_incoming_reference_request(
        third_admin_unit_id
    )

    url = utils.get_url(
        "api_v1_organization_incoming_event_reference_request_reject",
        id=admin_unit_id,
        event_reference_request_id=reference_request_id,
    )
    utils.assert_response_notFound(
        utils.post_json(url, {"rejection_reason": "duplicate"})
    )
