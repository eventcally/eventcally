import pytest

from tests.integration.utils import UtilActions


def test_profile(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    seeder.create_event(admin_unit_id)

    url = utils.get_url("main.profile", id=1)
    utils.get_ok(url)


def test_organization_invitation(client, seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url("main.user_organization_invitation", id=invitation_id)
    response = utils.get(url)
    utils.assert_response_redirect(
        response,
        "user.organization_invitation_negotiate",
        organization_invitation_id=invitation_id,
    )

    utils.get_endpoint_ok(
        "user.organization_invitation_negotiate",
        organization_invitation_id=invitation_id,
    )


def test_organization_invitation_not_registered(client, app, utils, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url("main.user_organization_invitation", id=invitation_id)
    response = client.get(url)
    utils.assert_response_redirect(response, "security.register")


def test_organization_invitation_not_authenticated(client, app, utils, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    url = utils.get_url("main.user_organization_invitation", id=invitation_id)

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

    url = utils.get_url("main.user_organization_invitation", id=invitation_id)
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

    url = utils.get_url("user.organization_invitations")
    utils.get_ok(url)


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
