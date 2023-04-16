import pytest


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
    utils.assert_response_redirect(response, "security.login", next=url)


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


def test_user_notifications(client, seeder, utils, app):
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

        place = User.query.get(user_id)
        assert not place.newsletter_enabled


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
