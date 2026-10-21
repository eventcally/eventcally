import pytest

from project.infrastructure.extensions import limiter

REPORT = {
    "contact_name": "Firstname Lastname",
    "contact_email": "firstname.lastname@test.de",
    "message": "Diese Veranstaltung wird nicht stattfinden.",
}


@pytest.fixture(autouse=True)
def reset_limiter(app):
    with app.app_context():
        limiter.reset()
    yield
    with app.app_context():
        limiter.reset()


def _create_event(seeder, utils, log_in=False, **kwargs):
    user_id, admin_unit_id = seeder.setup_base(log_in=log_in)
    event_id = seeder.create_event(admin_unit_id, **kwargs)
    # The report page is the Vue 3 shell that hands out the CSRF token.
    utils.get_ok(utils.get_url("main.event_report", event_id=event_id))
    return event_id


def _form_url(event_id):
    return f"/bff/public/events/{event_id}/report-form"


def _reports_url(event_id):
    return f"/bff/public/events/{event_id}/reports"


def test_report_form_anonymous(client, seeder, utils):
    event_id = _create_event(seeder, utils)

    body = utils.get_json_ok(_form_url(event_id)).json

    assert body["event_id"] == event_id
    assert body["event_name"]


def test_report_form_unknown_event(client, seeder, utils):
    seeder.setup_base(log_in=False)

    response = utils.get_json(_form_url(4711))

    utils.assert_response_notFound(response)
    assert response.json["name"] == "Not Found"


def test_report_form_draft_anonymous(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id, draft=True)

    response = utils.get_json(_form_url(event_id))

    utils.assert_response_unauthorized(response)
    assert response.json["name"] == "Unauthorized"


def test_report_anonymous_sends_mail(client, seeder, utils):
    event_id = _create_event(seeder, utils)
    seeder.create_user(email="admin@test.de", admin=True)
    seeder.create_user(email="normal@test.de", admin=False)

    response = utils.post_json(_reports_url(event_id), REPORT)

    utils.assert_response_no_content(response)
    utils.assert_send_mail_called(
        ["test@test.de", "admin@test.de"],
        [
            "Firstname Lastname",
            "firstname.lastname@test.de",
            "Diese Veranstaltung wird nicht stattfinden.",
        ],
    )


def test_report_logged_in(client, seeder, utils):
    event_id = _create_event(seeder, utils, log_in=True)

    response = utils.post_json(_reports_url(event_id), REPORT)

    utils.assert_response_no_content(response)


def test_report_without_csrf(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(log_in=False)
    event_id = seeder.create_event(admin_unit_id)

    response = client.post(_reports_url(event_id), json=REPORT)

    utils.assert_response_bad_request(response)


def test_report_validation(client, seeder, utils):
    event_id = _create_event(seeder, utils)

    response = utils.post_json(
        _reports_url(event_id),
        {"contact_name": "abc", "contact_email": "nope", "message": "short"},
    )

    utils.assert_response_unprocessable_entity(response)
    locs = [e["loc"] for e in response.json["errors"]]
    assert ["contact_name"] in locs
    assert ["contact_email"] in locs
    assert ["message"] in locs


def test_report_unknown_event(client, seeder, utils):
    _create_event(seeder, utils)

    response = utils.post_json(_reports_url(4711), REPORT)

    utils.assert_response_notFound(response)


def test_report_rate_limited(client, seeder, utils):
    event_id = _create_event(seeder, utils)

    for _ in range(5):
        utils.assert_response_no_content(
            utils.post_json(_reports_url(event_id), REPORT)
        )

    response = utils.post_json(_reports_url(event_id), REPORT)

    assert response.status_code == 429
    assert response.json["name"] == "Too Many Requests"
