import pytest


def test_create(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        mail_mock = utils.mock_send_mails(mocker)
        email = "new@member.de"
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 302
        utils.assert_send_mail_called(mail_mock, email)

        with app.app_context():
            from project.services.admin_unit import find_admin_unit_member_invitation

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation.roles == "admin"


def test_create_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)
        email = "new@member.de"
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "roles": "admin",
                "submit": "Submit",
            },
        )
        assert response.status_code == 200
        assert b"MockException" in response.data


def test_create_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = "/manage/admin_unit/%d/members/invite" % admin_unit_id
    response = client.get(url)
    assert response.status_code == 302


def test_read_accept(client, app, db, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    new_member_user_id = seeder.create_user(email)
    utils.login(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "accept": "Akzeptieren",
            },
        )
        utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)

        with app.app_context():
            from project.services.admin_unit import (
                find_admin_unit_member_invitation,
                get_member_for_admin_unit_by_user_id,
            )

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation is None

            member = get_member_for_admin_unit_by_user_id(
                admin_unit_id, new_member_user_id
            )
            assert len(member.roles) == 1
            assert any(r.name == "admin" for r in member.roles)


def test_read_accept_WrongRole(client, app, db, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    seeder.create_user(email)
    utils.login(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email, ["wrongrole"])

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "accept": "Akzeptieren",
            },
        )
        utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)


def test_read_decline(client, app, db, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    new_member_user_id = seeder.create_user(email)
    utils.login(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "decline": "Ablehnen",
            },
        )
        assert response.status_code == 302
        assert response.headers["Location"] == "http://localhost/manage"

        with app.app_context():
            from project.services.admin_unit import (
                find_admin_unit_member_invitation,
                get_member_for_admin_unit_by_user_id,
            )

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation is None

            member = get_member_for_admin_unit_by_user_id(
                admin_unit_id, new_member_user_id
            )
            assert member is None


def test_read_db_error(client, app, utils, seeder, mocker):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    seeder.create_user(email)
    utils.login(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "accept": "Akzeptieren",
            },
        )

        assert response.status_code == 200
        assert b"MockException" in response.data


def test_read_new_member_not_registered(client, app, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"] == "http://localhost/register"


def test_read_new_member_not_authenticated(client, app, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    seeder.create_user(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    assert response.status_code == 302
    assert response.headers["Location"].startswith("http://localhost/login")


@pytest.mark.parametrize("user_exists", [True, False])
def test_read_currentUserDoesNotMatchInvitationEmail(
    client, app, db, utils, seeder, user_exists
):
    user_id = seeder.create_user()
    utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    if user_exists:
        seeder.create_user(email)

    url = "/invitations/%d" % invitation_id
    environ, response = client.get(url, follow_redirects=True, as_tuple=True)

    assert environ["REQUEST_URI"] == "/profile"
    utils.assert_response_ok(response)
    utils.assert_response_contains(
        response, "Die Einladung wurde für einen anderen Nutzer ausgestellt."
    )


def test_delete(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/manage/invitation/%d/delete" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "submit": "Submit",
            },
        )
        assert response.status_code == 302

        with app.app_context():
            from project.services.admin_unit import find_admin_unit_member_invitation

            invitation = find_admin_unit_member_invitation(email, admin_unit_id)
            assert invitation is None


def test_delete_db_error(client, app, utils, seeder, mocker):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/manage/invitation/%d/delete" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        utils.mock_db_commit(mocker)

        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": email,
                "submit": "Submit",
            },
        )

        assert response.status_code == 200
        assert b"MockException" in response.data


def test_delete_email_does_not_match(client, app, utils, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/manage/invitation/%d/delete" % invitation_id
    response = client.get(url)
    assert response.status_code == 200

    with client:
        response = client.post(
            url,
            data={
                "csrf_token": utils.get_csrf(response),
                "email": "wrong@test.de",
                "submit": "Submit",
            },
        )
        assert response.status_code == 200
        assert b"Die eingegebene Email passt nicht zur Email" in response.data


def test_delete_permission_missing(client, app, db, utils, seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    email = "new@member.de"
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/manage/invitation/%d/delete" % invitation_id

    response = client.get(url)
    assert response.status_code == 302
