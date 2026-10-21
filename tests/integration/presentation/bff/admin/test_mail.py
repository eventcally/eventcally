import pytest

from project.application.read_models.mail_job_read_models import MailJobStatusReadModel

JOB_ID = "00000000-0000-4000-8000-000000000000"


def _login_admin(seeder, utils):
    seeder.create_user(admin=True)
    utils.login()
    utils.get_ok("/admin-next/email")  # picks up the CSRF token of the Vue 3 shell


def _login_non_admin(seeder, utils):
    seeder.create_user()
    utils.login()
    utils.get_ok("/")


def test_mail_config(app, client, seeder, utils):
    _login_admin(seeder, utils)
    previous = app.config.get("MAIL_PASSWORD")
    app.config["MAIL_PASSWORD"] = "s3cret"

    try:
        response = utils.get_json_ok("/bff/admin/email")
    finally:
        app.config["MAIL_PASSWORD"] = previous

    assert response.json["password_set"] is True
    assert b"s3cret" not in response.data
    assert set(response.json) == {
        "suppress_send",
        "server",
        "port",
        "use_tls",
        "use_ssl",
        "username",
        "password_set",
        "default_sender",
    }


def test_mail_config_without_password(app, client, seeder, utils):
    _login_admin(seeder, utils)
    previous = app.config.get("MAIL_PASSWORD")
    app.config["MAIL_PASSWORD"] = None

    try:
        response = utils.get_json_ok("/bff/admin/email")
    finally:
        app.config["MAIL_PASSWORD"] = previous

    assert response.json["password_set"] is False


@pytest.mark.parametrize(
    "sender,expected",
    [
        (("EventCally", "info@test.de"), "EventCally info@test.de"),
        ("info@test.de", "info@test.de"),
        (None, None),
    ],
)
def test_mail_config_default_sender(app, client, seeder, utils, sender, expected):
    _login_admin(seeder, utils)
    previous = app.config.get("MAIL_DEFAULT_SENDER")
    app.config["MAIL_DEFAULT_SENDER"] = sender

    try:
        response = utils.get_json_ok("/bff/admin/email")
    finally:
        app.config["MAIL_DEFAULT_SENDER"] = previous

    assert response.json["default_sender"] == expected


def test_send_test_mail_sync(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json("/bff/admin/email/test", {"recipient": "test@test.de"})

    utils.assert_response_ok(response)
    assert response.json == {"job_id": None, "count": 1}
    utils.assert_send_mail_called("test@test.de")


def test_send_test_mail_sync_failure(app, client, seeder, utils, mocker):
    _login_admin(seeder, utils)
    mocker.patch.object(
        app.test_email_service,
        "send_mails_with_signatures",
        side_effect=Exception("SMTP down"),
    )

    response = utils.post_json("/bff/admin/email/test", {"recipient": "test@test.de"})

    utils.assert_response_bad_request(response)
    assert response.json["name"] == "MailDeliveryError"
    assert "SMTP down" in response.json["message"]


def test_send_test_mail_async(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json(
        "/bff/admin/email/test", {"recipient": "test@test.de", "asynchronous": True}
    )

    utils.assert_response_ok(response)
    assert response.json == {"job_id": JOB_ID, "count": 1}
    utils.assert_send_mail_called("test@test.de")


def test_send_test_mail_invalid_email(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json("/bff/admin/email/test", {"recipient": "nope"})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["recipient"]


def test_newsletter_info(client, seeder, utils):
    _login_admin(seeder, utils)
    for i in range(3):
        seeder.create_user(email=f"user{i}@test.de")

    response = utils.get_json_ok("/bff/admin/newsletter")

    assert response.json == {"recipient_count": 4}


def test_send_newsletter_test(app, client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json(
        "/bff/admin/newsletter",
        {"audience": "test", "test_recipient": "other@test.de", "message": "<p>Hi</p>"},
    )

    utils.assert_response_ok(response)
    assert response.json["count"] == 1
    utils.assert_send_mail_called("other@test.de", "<p>Hi</p>")


def test_send_newsletter_all(app, client, seeder, utils):
    _login_admin(seeder, utils)
    for i in range(2):
        seeder.create_user(email=f"user{i}@test.de")
    count = utils.get_json_ok("/bff/admin/newsletter").json["recipient_count"]

    response = utils.post_json(
        "/bff/admin/newsletter", {"audience": "all", "message": "<p>Hi</p>"}
    )

    utils.assert_response_ok(response)
    assert response.json["count"] == count == 3
    sent = {m["recipient"] for m in app.test_email_service.sent_emails}
    assert sent == {"test@test.de", "user0@test.de", "user1@test.de"}


def test_send_newsletter_test_without_recipient(app, client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json(
        "/bff/admin/newsletter", {"audience": "test", "message": "Hi"}
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["test_recipient"]
    assert app.test_email_service.sent_emails == []


def test_send_newsletter_all_with_recipient(app, client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json(
        "/bff/admin/newsletter",
        {"audience": "all", "test_recipient": "other@test.de", "message": "Hi"},
    )

    utils.assert_response_unprocessable_entity(response)
    assert app.test_email_service.sent_emails == []


def test_send_newsletter_missing_audience(app, client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json("/bff/admin/newsletter", {"message": "Hi"})

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["audience"]
    assert app.test_email_service.sent_emails == []


def test_send_newsletter_empty_message(client, seeder, utils):
    _login_admin(seeder, utils)

    response = utils.post_json(
        "/bff/admin/newsletter",
        {"audience": "test", "test_recipient": "other@test.de", "message": ""},
    )

    utils.assert_response_unprocessable_entity(response)
    assert response.json["errors"][0]["loc"] == ["message"]


@pytest.fixture
def fake_status_reader(app):
    from dependency_injector import providers

    from project.application.services.abstract_mail_job_status_reader import (
        AbstractMailJobStatusReader,
    )

    class FakeReader(AbstractMailJobStatusReader):
        def get(self, job_id):
            if job_id != JOB_ID:
                return None
            return MailJobStatusReadModel(
                job_id=job_id, count=3, completed=1, ready=False
            )

    app.container.services.mail_job_status_reader.override(
        providers.Object(FakeReader())
    )
    yield
    app.container.services.mail_job_status_reader.reset_override()


def test_mail_job_status(client, seeder, utils, fake_status_reader):
    _login_admin(seeder, utils)

    response = utils.get_json_ok(f"/bff/admin/mail-jobs/{JOB_ID}")

    assert response.json == {
        "job_id": JOB_ID,
        "count": 3,
        "completed": 1,
        "ready": False,
        "successful": None,
    }


def test_mail_job_status_unknown(client, seeder, utils, fake_status_reader):
    _login_admin(seeder, utils)

    utils.assert_response_notFound(
        utils.get_json("/bff/admin/mail-jobs/00000000-0000-4000-8000-000000000001")
    )


def test_mail_job_status_malformed_id(client, seeder, utils, fake_status_reader):
    _login_admin(seeder, utils)

    utils.assert_response_notFound(utils.get_json("/bff/admin/mail-jobs/not-a-uuid"))


GET_ROUTES = [
    "/bff/admin/email",
    "/bff/admin/newsletter",
    f"/bff/admin/mail-jobs/{JOB_ID}",
]
POST_ROUTES = [
    ("/bff/admin/email/test", {"recipient": "test@test.de"}),
    ("/bff/admin/newsletter", {"audience": "all", "message": "Hi"}),
]


@pytest.mark.parametrize("url", GET_ROUTES)
def test_get_forbidden(client, seeder, utils, url):
    _login_non_admin(seeder, utils)

    utils.assert_response_forbidden(utils.get_json(url))


@pytest.mark.parametrize("url,data", POST_ROUTES)
def test_post_forbidden(app, client, seeder, utils, url, data):
    _login_non_admin(seeder, utils)

    utils.assert_response_forbidden(utils.post_json(url, data))
    assert app.test_email_service.sent_emails == []


@pytest.mark.parametrize("url", GET_ROUTES)
def test_get_unauthorized(client, utils, url):
    utils.assert_response_unauthorized(utils.get_json(url))


@pytest.mark.parametrize("url,data", POST_ROUTES)
def test_post_unauthorized(client, utils, url, data):
    utils.assert_response_unauthorized(utils.post_json(url, data))


@pytest.mark.parametrize("url,data", POST_ROUTES)
def test_post_without_csrf(app, client, seeder, utils, url, data):
    seeder.create_user(admin=True)
    utils.login()

    utils.assert_response_bad_request(utils.post_json(url, data))
    assert app.test_email_service.sent_emails == []
