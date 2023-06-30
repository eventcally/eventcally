import pytest


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("is_verified", [True, False])
def test_review_verify(client, seeder, utils, app, mocker, db, db_error, is_verified):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url("event_reference_request_review", id=reference_request_id)

    if is_verified:
        with app.app_context():
            from project.models import (
                EventReferenceRequest,
                EventReferenceRequestReviewStatus,
            )

            reference_request = db.session.get(
                EventReferenceRequest, reference_request_id
            )
            reference_request.review_status = EventReferenceRequestReviewStatus.verified
            db.session.commit()

        response = client.get(url)
        utils.assert_response_redirect(
            response, "manage_admin_unit_reference_requests_incoming", id=admin_unit_id
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
        response, "manage_admin_unit_reference_requests_incoming", id=admin_unit_id
    )
    utils.assert_send_mail_called(mail_mock, "other@test.de")

    with app.app_context():
        from project.models import (
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )
        from project.services.admin_unit import get_admin_unit_relation

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert reference_request.verified

        reference = db.session.get(EventReference, reference_request_id)
        assert reference.event_id == event_id
        assert reference.admin_unit_id == admin_unit_id

        relation = get_admin_unit_relation(
            reference.admin_unit_id, reference.event.admin_unit_id
        )
        assert relation is not None
        assert relation.auto_verify_event_reference_requests


def test_review_reject(client, seeder, utils, app, db, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url("event_reference_request_review", id=reference_request_id)
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
        response, "manage_admin_unit_reference_requests_incoming", id=admin_unit_id
    )

    with app.app_context():
        from project.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = db.session.get(EventReferenceRequest, reference_request_id)
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.rejected
        )
        assert reference_request.rejection_reason is None


def test_review_status(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(admin_unit_id)

    url = utils.get_url(
        "event_reference_request_review_status", id=reference_request_id
    )
    utils.get_ok(url)


def test_review_status_401_third(client, seeder, utils):
    seeder.create_user()
    seeder._utils.login()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(third_admin_unit_id)

    url = utils.get_url(
        "event_reference_request_review_status", id=reference_request_id
    )
    response = client.get(url)
    assert response.status_code == 401


def test_review_status_401_unauthorized(client, seeder, utils):
    seeder.create_user()

    third_user_id = seeder.create_user("third@third.de")
    third_admin_unit_id = seeder.create_admin_unit(third_user_id, "Third Crew")
    (
        other_user_id,
        other_admin_unit_id,
        event_id,
        reference_request_id,
    ) = seeder.create_incoming_reference_request(third_admin_unit_id)

    url = utils.get_url(
        "event_reference_request_review_status", id=reference_request_id
    )
    response = client.get(url)
    assert response.status_code == 401
