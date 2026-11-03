import datetime

import pytest

from tests.integration.presentation.bff.user.helpers import flashes, shell

PROFILE = "/bff/user/profile"
GENERAL = "/bff/user/settings/general"
NOTIFICATIONS = "/bff/user/settings/notifications"
REQUEST_DELETION = "/bff/user/deletion"
CANCEL_DELETION = "/bff/user/deletion/cancel"
ACCEPT_TOS = "/bff/user/accept-tos"


def _user(app, db, user_id):
    from project.infrastructure.models import User

    with app.app_context():
        user = db.session.get(User, user_id)
        return user.locale, user.newsletter_enabled, user.deletion_requested_at


def _request_deletion(app, db, user_id):
    from project.infrastructure.models import User

    with app.app_context():
        user = db.session.get(User, user_id)
        user.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()


# access


def test_anonymous_is_401(client, utils):
    assert utils.get_json(PROFILE).status_code == 401
    assert utils.get_json(ACCEPT_TOS).status_code == 401
    assert utils.put_json(GENERAL, {}).status_code == 401
    assert utils.post_json(REQUEST_DELETION, {"email": "a@b.de"}).status_code == 401


def test_writes_require_csrf(client, seeder, utils):
    seeder.setup_base()

    assert utils.put_json(GENERAL, {"locale": "de"}).status_code == 400
    assert (
        utils.put_json(NOTIFICATIONS, {"newsletter_enabled": True}).status_code == 400
    )
    assert utils.post_json(REQUEST_DELETION, {"email": "a@b.de"}).status_code == 400
    assert utils.post_json(CANCEL_DELETION, {"email": "a@b.de"}).status_code == 400
    assert utils.post_json(ACCEPT_TOS, {"accept_tos": True}).status_code == 400


# profile


def test_profile(client, seeder, utils):
    seeder.setup_base()

    body = utils.get_json_ok(PROFILE).json

    assert body["email"] == "test@test.de"
    assert body["locale"] is None
    assert body["deletion_requested_at"] is None


def test_profile_with_requested_deletion(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    _request_deletion(app, db, user_id)

    assert utils.get_json_ok(PROFILE).json["deletion_requested_at"] is not None


# settings


@pytest.mark.parametrize("locale", ["de", "en", None])
def test_update_general_settings(client, app, db, seeder, utils, locale):
    user_id, _ = seeder.setup_base()
    shell(utils)

    response = utils.put_json(GENERAL, {"locale": locale})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/profile"}
    assert _user(app, db, user_id)[0] == locale
    assert [category for category, _ in flashes(client)] == ["success"]


def test_update_general_settings_rejects_unknown_locale(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    response = utils.put_json(GENERAL, {"locale": "xx"})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["locale"]


@pytest.mark.parametrize("enabled", [True, False])
def test_update_notification_settings(client, app, db, seeder, utils, enabled):
    user_id, _ = seeder.setup_base()
    shell(utils)

    response = utils.put_json(NOTIFICATIONS, {"newsletter_enabled": enabled})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/profile"}
    assert _user(app, db, user_id)[1] is enabled
    assert flashes(client) == [("success", "Einstellungen erfolgreich aktualisiert")]


# deletion


def test_request_deletion(client, app, db, seeder, utils):
    _, _, member_id = seeder.setup_base_event_verifier()
    shell(utils)

    response = utils.post_json(REQUEST_DELETION, {"email": "TEST@test.de"})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/profile"}
    assert _user(app, db, member_id)[2] is not None

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    assert [m["recipient"] for m in app.test_email_service.sent_emails] == [
        "test@test.de"
    ]


def test_request_deletion_with_another_email_is_422(client, app, db, seeder, utils):
    _, _, member_id = seeder.setup_base_event_verifier()
    shell(utils)

    response = utils.post_json(REQUEST_DELETION, {"email": "wrong@test.de"})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["email"]
    assert (
        response.json["errors"][0]["msg"]
        == "Die eingegebene Email entspricht nicht deiner Email"
    )
    assert _user(app, db, member_id)[2] is None


def test_request_deletion_of_an_administrator_is_400(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    shell(utils)

    response = utils.post_json(REQUEST_DELETION, {"email": "test@test.de"})

    assert response.status_code == 400
    assert "Administrator" in response.json["message"]
    assert _user(app, db, user_id)[2] is None


def test_request_deletion_twice_is_400(client, app, db, seeder, utils):
    _, _, member_id = seeder.setup_base_event_verifier()
    shell(utils)
    _request_deletion(app, db, member_id)

    response = utils.post_json(REQUEST_DELETION, {"email": "test@test.de"})

    assert response.status_code == 400


def test_cancel_deletion(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    shell(utils)
    _request_deletion(app, db, user_id)

    response = utils.post_json(CANCEL_DELETION, {"email": "test@test.de"})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/profile"}
    assert _user(app, db, user_id)[2] is None


def test_cancel_deletion_with_another_email_is_422(client, app, db, seeder, utils):
    user_id, _ = seeder.setup_base()
    shell(utils)
    _request_deletion(app, db, user_id)

    response = utils.post_json(CANCEL_DELETION, {"email": "wrong"})

    assert response.status_code == 422
    assert _user(app, db, user_id)[2] is not None


def test_cancel_deletion_without_request_is_400(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    assert (
        utils.post_json(CANCEL_DELETION, {"email": "test@test.de"}).status_code == 400
    )


# accept ToS


def _login_without_tos(seeder, utils):
    seeder.create_user(tos_accepted=False)
    utils.login()
    # The ToS gate redirects every page but the confirmation page, which carries the token.
    utils.get_ok("/user/accept-tos?next=/manage")


def test_accept_tos_endpoints_pass_the_gate_by_name(app):
    # The gate exempts the endpoints by name; they follow the view function names.
    endpoints = {rule.endpoint for rule in app.url_map.iter_rules()}

    assert "bff.bff_user.get_accept_tos" in endpoints
    assert "bff.bff_user.accept_tos" in endpoints


@pytest.mark.parametrize("has_tos", [False, True])
def test_get_accept_tos(client, app, db, seeder, utils, has_tos):
    from project.infrastructure.models import Settings

    _login_without_tos(seeder, utils)

    if has_tos:
        with app.app_context():
            db.session.add(Settings(tos="Terms"))
            db.session.commit()

    response = utils.get_json(ACCEPT_TOS)

    assert response.status_code == 200
    assert response.json == {"has_tos": has_tos}


def test_accept_tos(client, app, db, seeder, utils):
    _login_without_tos(seeder, utils)

    response = utils.post_json(f"{ACCEPT_TOS}?next=/manage", {"accept_tos": True})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/manage"}

    with app.app_context():
        from project.infrastructure.models import User

        assert User.query.filter(User.email == "test@test.de").one().tos_accepted_at


def test_accept_tos_ignores_an_external_next(client, seeder, utils):
    _login_without_tos(seeder, utils)

    response = utils.post_json(
        f"{ACCEPT_TOS}?next=https://evil.example/", {"accept_tos": True}
    )

    assert response.status_code == 200
    assert "evil" not in response.json["redirect_url"]


def test_accept_tos_needs_the_checkbox(client, app, db, seeder, utils):
    _login_without_tos(seeder, utils)

    response = utils.post_json(ACCEPT_TOS, {"accept_tos": False})

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["accept_tos"]


def test_accept_tos_again_only_redirects(client, seeder, utils):
    seeder.setup_base()
    shell(utils)

    response = utils.post_json(f"{ACCEPT_TOS}?next=/manage", {"accept_tos": True})

    assert response.status_code == 200
    assert response.json == {"redirect_url": "/manage"}


def test_a_database_error_is_400(client, seeder, utils, mocker):
    seeder.setup_base()
    shell(utils)
    utils.mock_db_commit(mocker)

    response = utils.put_json(NOTIFICATIONS, {"newsletter_enabled": False})

    assert response.status_code == 400
