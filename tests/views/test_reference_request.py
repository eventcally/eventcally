import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


@pytest.mark.parametrize("db_error", [True, False])
def test_create(client, app, utils: UtilActions, seeder: Seeder, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)

    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("event_reference_request_create", event_id=event_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    mail_mock = utils.mock_send_mails_async(mocker)
    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": other_admin_unit_id},
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_reference_requests_outgoing", id=admin_unit_id
    )
    utils.assert_send_mail_called(mail_mock, "other@test.de")

    with app.app_context():
        from project.models import (
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = (
            EventReferenceRequest.query.filter(
                EventReferenceRequest.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReferenceRequest.event_id == event_id)
            .first()
        )
        assert reference_request is not None
        assert (
            reference_request.review_status == EventReferenceRequestReviewStatus.inbox
        )


def test_create_duplicateNotAllowed(client, app, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    # First
    url = utils.get_url("event_reference_request_create", event_id=event_id)
    response = utils.get_ok(url)
    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": other_admin_unit_id},
    )
    utils.assert_response_redirect(
        response, "manage_admin_unit_reference_requests_outgoing", id=admin_unit_id
    )

    # Second
    url = utils.get_url("event_reference_request_create", event_id=event_id)
    response = utils.get_ok(url)
    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": other_admin_unit_id},
    )
    utils.assert_response_ok(response)
    assert b"duplicate key" in response.data


def test_create_unverifiedAdminUnitNotAllowed(
    client, app, utils: UtilActions, seeder: Seeder
):
    _, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    seeder.create_admin_unit(other_user_id, "Other Crew")

    url = utils.get_url("event_reference_request_create", event_id=event_id)
    response = utils.get(url)
    utils.assert_response_unauthorized(response)


def test_create_autoVerify(client, app, utils: UtilActions, seeder: Seeder, mocker):
    user_id, admin_unit_id = seeder.setup_base()
    event_id = seeder.create_event(admin_unit_id)
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    seeder.create_admin_unit_relation(other_admin_unit_id, admin_unit_id, True)

    mail_mock = utils.mock_send_mails_async(mocker)
    url = utils.get_url("event_reference_request_create", event_id=event_id)
    response = utils.get_ok(url)
    response = utils.post_form(
        url,
        response,
        {"admin_unit_id": other_admin_unit_id},
    )
    utils.assert_response_redirect(
        response, "manage_admin_unit_reference_requests_outgoing", id=admin_unit_id
    )
    utils.assert_send_mail_called(mail_mock, "other@test.de")

    with app.app_context():
        from project.models import (
            EventReference,
            EventReferenceRequest,
            EventReferenceRequestReviewStatus,
        )

        reference_request = (
            EventReferenceRequest.query.filter(
                EventReferenceRequest.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReferenceRequest.event_id == event_id)
            .first()
        )
        assert reference_request is not None
        assert (
            reference_request.review_status
            == EventReferenceRequestReviewStatus.verified
        )

        reference = (
            EventReference.query.filter(
                EventReference.admin_unit_id == other_admin_unit_id
            )
            .filter(EventReference.event_id == event_id)
            .first()
        )
        assert reference is not None


def test_admin_unit_reference_requests_incoming(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_incoming_reference_request(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit_reference_requests_incoming", id=admin_unit_id
    )


def test_admin_unit_reference_requests_outgoing(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_outgoing_reference_request(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit_reference_requests_outgoing", id=admin_unit_id
    )
