import pytest

from tests.integration.utils import UtilActions


def test_create_is_a_shell(client, utils: UtilActions, seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.organization_member_invitation_create", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_list_is_a_shell(client, utils: UtilActions, seeder):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.organization_member_invitations", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_update_and_delete_pages_are_gone(client, utils: UtilActions, seeder):
    """Changing the roles and revoking are modals of the list."""
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")

    for action in ("update", "delete"):
        utils.assert_response_notFound(
            utils.get(
                f"/manage/admin_unit/{admin_unit_id}/organization_member_invitation/{invitation_id}/{action}"
            )
        )


def test_list(client, app, db, utils: UtilActions, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    _ = seeder.create_user(email)
    utils.login(email)

    _ = seeder.create_invitation(admin_unit_id, email)
    utils.get_endpoint_ok("user.organization_member_invitations")


def test_read_leads_to_the_negotiate_page(client, app, db, utils: UtilActions, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    seeder.create_user(email)
    utils.login(email)

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    response = utils.get_endpoint("main.admin_unit_member_invitation", id=invitation_id)
    utils.assert_response_redirect(
        response,
        "user.organization_member_invitation_negotiate",
        organization_member_invitation_id=invitation_id,
    )

    utils.get_endpoint_ok(
        "user.organization_member_invitation_negotiate",
        organization_member_invitation_id=invitation_id,
    )


def test_read_new_member_not_registered(client, app, utils: UtilActions, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    email = "new@member.de"

    invitation_id = seeder.create_invitation(admin_unit_id, email)

    url = "/invitations/%d" % invitation_id
    response = client.get(url)
    utils.assert_response_redirect(response, "security.register")


def test_read_new_member_not_authenticated(client, app, utils: UtilActions, seeder):
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
    client, app, db, utils: UtilActions, seeder, user_exists
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


def test_invitation_link_of_unknown_invitation(seeder, utils):
    seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(utils.get_url("main.admin_unit_member_invitation", id=4711))
    )
