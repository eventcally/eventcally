import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_create(client, app, utils: UtilActions, seeder, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.organization_member_invitation_create", id=admin_unit_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "email": "invited@test.de",
            "roles": "admin",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_member_invitations", id=admin_unit_id
    )

    utils.get_endpoint_ok(
        "manage_admin_unit.organization_member_invitations", id=admin_unit_id
    )

    with app.app_context():
        from project.services.admin_unit import find_admin_unit_member_invitation

        invitation = find_admin_unit_member_invitation("invited@test.de", admin_unit_id)
        assert invitation.roles == "admin"
        assert invitation is not None

    invitation_url = utils.get_url(
        "admin_unit_member_invitation",
        id=invitation.id,
    )
    utils.assert_send_mail_called(mail_mock, "invited@test.de", invitation_url)


def test_update(client, app, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")

    url = utils.get_url(
        "manage_admin_unit.organization_member_invitation_update",
        id=admin_unit_id,
        organization_member_invitation_id=invitation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "roles": "admin",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_member_invitations", id=admin_unit_id
    )


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
        utils.assert_response_redirect(response, "manage")

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
    utils.assert_response_redirect(response, "security.register")


def test_read_new_member_not_authenticated(client, app, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    seeder.create_user(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    utils.assert_response_redirect_to_login(response, url)


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
    response = client.get(url, follow_redirects=True)

    utils.assert_response_ok(response)
    utils.assert_response_contains(
        response, "Die Einladung wurde für einen anderen Nutzer ausgestellt."
    )
