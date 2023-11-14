import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_profile(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("profile", id=1)
    utils.get_ok(url)


def test_organization_invitation_not_registered(client, app, utils, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url("user_organization_invitation", id=invitation_id)
    response = client.get(url)
    utils.assert_response_redirect(response, "security.register")


def test_organization_invitation_not_authenticated(client, app, utils, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    url = utils.get_url("user_organization_invitation", id=invitation_id)

    response = client.get(url)
    utils.assert_response_redirect_to_login(response, url)


@pytest.mark.parametrize("user_exists", [True, False])
def test_organization_invitation_currentUserDoesNotMatchInvitationEmail(
    client, app, db, utils, seeder, user_exists
):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    if user_exists:
        seeder.create_user("invited@test.de")

    url = utils.get_url("user_organization_invitation", id=invitation_id)
    response = client.get(url, follow_redirects=True)

    utils.assert_response_ok(response)
    utils.assert_response_contains(
        response, "Die Einladung wurde für einen anderen Nutzer ausgestellt."
    )


def test_organization_invitation_list(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    _ = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url("user_organization_invitations")
    utils.get_ok(url)


def test_user_favorite_events(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("user_favorite_events")
    utils.get_ok(url)


@pytest.mark.parametrize("locale", [None, "de"])
def test_user_general(client, seeder, utils, app, db, locale):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("user_general")
    response = utils.get_ok(url)

    if locale is None:
        values = dict()
    else:
        values = {
            "locale": locale,
        }

    response = utils.post_form(
        url,
        response,
        values,
    )

    utils.assert_response_redirect(response, "profile")

    with app.app_context():
        from project.models import User

        user = db.session.get(User, user_id)
        assert user.locale == locale


def test_user_notifications(client, seeder, utils, app, db):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("user_notifications")
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "newsletter_enabled": None,
        },
    )

    utils.assert_response_redirect(response, "profile")

    with app.app_context():
        from project.models import User

        user = db.session.get(User, user_id)
        assert not user.newsletter_enabled


def test_login_flash(client, seeder, utils):
    email = "test@test.de"
    password = "MeinPasswortIstDasBeste"
    seeder.create_user(email, password, confirm=False)

    response = client.get("/login")
    assert response.status_code == 200

    with client:
        response = client.post(
            "/login",
            data={
                "email": email,
                "password": password,
                "csrf_token": utils.get_csrf(response),
                "submit": "Anmelden",
            },
        )

    utils.assert_response_error_message(
        response, "Beachte, dass du deine E-Mail-Adresse bestätigen muss."
    )


def test_forgot_reset_flash(client, seeder, utils):
    email = "test@test.de"
    password = "MeinPasswortIstDasBeste"
    seeder.create_user(email, password, confirm=False)

    response = client.get("/login")
    assert response.status_code == 200

    with client:
        response = client.post(
            "/reset",
            data={
                "email": email,
                "csrf_token": utils.get_csrf(response),
                "submit": "Passwort wiederherstellen",
            },
        )

    utils.assert_response_error_message(
        response, "Beachte, dass du deine E-Mail-Adresse bestätigen muss."
    )


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_user_request_deletion(
    client, seeder: Seeder, utils, app, db, mocker, db_error, non_match
):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    url = utils.get_url("user_request_deletion")
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_email = "test@test.de"

    if non_match:
        form_email = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "email": form_email,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Die eingegebene Email entspricht nicht deiner Email"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "profile")

    with app.app_context():
        from project.models import User

        user = db.session.get(User, member_id)
        assert user.deletion_requested_at is not None


def test_user_request_deletion_admin_member(client, seeder: Seeder, utils, app, db):
    seeder.setup_base()

    url = utils.get_url("user_request_deletion")
    response = utils.get_ok(url)
    utils.assert_response_error_message(
        response,
        "Du bist Administrator von mindestens einer Organisation. Beende deine Mitgliedschaft, um deinen Account zu löschen.",
    )


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_user_cancel_deletion(
    client, seeder, utils, app, db, mocker, db_error, non_match
):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.models import User

        user = db.session.get(User, user_id)
        user.deletion_requested_at = datetime.datetime.utcnow()
        db.session.commit()

    url = utils.get_url("user_cancel_deletion")
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_email = "test@test.de"

    if non_match:
        form_email = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "email": form_email,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Die eingegebene Email entspricht nicht deiner Email"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "profile")

    with app.app_context():
        from project.models import User

        user = db.session.get(User, user_id)
        assert user.deletion_requested_at is None


def test_user_accept_tos(client, app, db, seeder: Seeder, utils: UtilActions):
    seeder.setup_base()

    with app.app_context():
        from project.services.admin import reset_tos_accepted_for_users

        reset_tos_accepted_for_users()

    response = utils.get_endpoint("profile")
    utils.assert_response_redirect(
        response, "user_accept_tos", next="http://localhost/profile"
    )

    response = utils.get_endpoint_ok("user_accept_tos", next="/profile")
    response = utils.post_form(
        response.request.url,
        response,
        {
            "accept_tos": "y",
            "submit": "Confirm",
        },
    )
    utils.assert_response_redirect(response, "profile")
