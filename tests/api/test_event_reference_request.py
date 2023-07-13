from tests.seeder import Seeder
from tests.utils import UtilActions


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
        from project.models import EventReferenceRequest

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
        from project.models import (
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
        from project.models import (
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
