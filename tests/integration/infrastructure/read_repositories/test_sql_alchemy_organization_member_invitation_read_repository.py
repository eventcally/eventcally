"""SqlAlchemyOrganizationMemberInvitationReadRepository against the database."""

import pytest

from project.application.queries import (
    ListOrganizationMemberInvitationsQuery,
    ListUserMemberInvitationsQuery,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.organization_member_invitation_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


@pytest.fixture
def invitations(seeder):
    owner_id, admin_unit_id = seeder.setup_base(log_in=False)
    zeta_id = seeder.create_invitation(
        admin_unit_id, "Zeta@test.de", ["event_verifier"]
    )
    alpha_id = seeder.create_invitation(
        admin_unit_id, "alpha@test.de", ["admin", "event_verifier"]
    )
    other_owner_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_owner_id, "Andere Crew")
    other_id = seeder.create_invitation(other_admin_unit_id, "ALPHA@test.de")
    return admin_unit_id, other_admin_unit_id, alpha_id, zeta_id, other_id


def test_list_is_scoped_and_ordered_by_email(read_repo, invitations):
    admin_unit_id, _, alpha_id, zeta_id, _ = invitations

    page = read_repo(
        "list", ListOrganizationMemberInvitationsQuery(admin_unit_id=admin_unit_id)
    )

    assert [item.id for item in page.items] == [alpha_id, zeta_id]
    assert page.items[0].roles == "admin,event_verifier"
    assert page.items[0].admin_unit.name == "Meine Crew"
    assert read_repo("organization_exists", admin_unit_id) is True
    assert read_repo("organization_exists", 4711) is False


def test_get_and_recipient(read_repo, invitations):
    admin_unit_id, _, _, zeta_id, _ = invitations

    invitation = read_repo("get", zeta_id)

    assert invitation.email == "Zeta@test.de"
    assert invitation.admin_unit_id == admin_unit_id
    assert invitation.roles == "event_verifier"
    assert read_repo("get", 4711) is None
    assert read_repo("get_recipient_email", zeta_id) == "Zeta@test.de"
    assert read_repo("get_recipient_email", 4711) is None


def test_list_for_user_matches_email_ignoring_case(read_repo, seeder, invitations):
    _, other_admin_unit_id, alpha_id, _, other_id = invitations
    alpha_user_id = seeder.create_user("Alpha@Test.de")

    page = read_repo(
        "list_for_user", ListUserMemberInvitationsQuery(user_id=alpha_user_id)
    )

    assert [item.id for item in page.items] == [alpha_id, other_id]
    assert page.items[1].admin_unit.id == other_admin_unit_id
