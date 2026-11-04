import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create(client, app, utils: UtilActions, seeder):
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
        from project.infrastructure.seed_helpers import (
            find_admin_unit_member_invitation,
        )

        invitation = find_admin_unit_member_invitation("invited@test.de", admin_unit_id)
        assert invitation.roles == "admin"
        assert invitation is not None

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    invitation_url = utils.get_url(
        "main.admin_unit_member_invitation",
        id=invitation.id,
    )

    assert len(app.test_email_service.sent_emails) == 1
    sent_email = app.test_email_service.sent_emails[0]
    assert sent_email["recipient"] == "invited@test.de"
    assert invitation_url in sent_email["body"]
    assert invitation_url in sent_email["html"]


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


def test_delete(client, app, db, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_invitation(admin_unit_id, "invited@test.de")

    url = utils.get_url(
        "manage_admin_unit.organization_member_invitation_delete",
        id=admin_unit_id,
        organization_member_invitation_id=invitation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "submit": "Submit",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_member_invitations", id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnitMemberInvitation

        assert db.session.get(AdminUnitMemberInvitation, invitation_id) is None


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
