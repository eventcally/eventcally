import pytest


def test_review(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_suggestion_id = seeder.create_event_suggestion(admin_unit_id)

    url = utils.get_url(
        "event_suggestion_review", event_suggestion_id=event_suggestion_id
    )
    utils.get_ok(url)


def test_review_status(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    event_suggestion_id = seeder.create_event_suggestion(admin_unit_id)

    url = utils.get_url(
        "event_suggestion_review_status", event_suggestion_id=event_suggestion_id
    )
    utils.get_ok(url)


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("is_verified", [True, False])
def test_reject(client, app, utils, seeder, mocker, db, db_error, is_verified):
    user_id, admin_unit_id = seeder.setup_base()
    event_suggestion_id = seeder.create_event_suggestion(admin_unit_id)

    url = utils.get_url(
        "event_suggestion_reject", event_suggestion_id=event_suggestion_id
    )

    if is_verified:
        with app.app_context():
            from project.models import EventReviewStatus, EventSuggestion

            suggestion = db.session.get(EventSuggestion, event_suggestion_id)
            suggestion.review_status = EventReviewStatus.verified
            db.session.commit()

        response = client.get(url)
        utils.assert_response_redirect(
            response, "event_suggestion_review", event_suggestion_id=event_suggestion_id
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
            "rejection_resaon": 0,
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit_event_reviews", id=admin_unit_id
    )
    utils.assert_send_mail_called(mail_mock, "vorname@nachname.de")

    with app.app_context():
        from project.models import EventReviewStatus, EventSuggestion

        suggestion = db.session.get(EventSuggestion, event_suggestion_id)
        assert suggestion.review_status == EventReviewStatus.rejected
        assert suggestion.rejection_resaon is None
