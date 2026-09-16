"""Unit tests for AdminUnitMemberInvitation command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.accept_member_invitation_handler import (
    AcceptMemberInvitationHandler,
)
from project.application.command_handlers.decline_member_invitation_handler import (
    DeclineMemberInvitationHandler,
)
from project.application.command_handlers.invite_user_to_organization_handler import (
    InviteUserToOrganizationHandler,
)
from project.application.command_handlers.revoke_member_invitation_handler import (
    RevokeMemberInvitationHandler,
)
from project.application.command_handlers.update_member_invitation_handler import (
    UpdateMemberInvitationHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission

ADMIN_UNIT_ID = 1
OTHER_USER_ID = 2


def _seed_invitation(
    uow, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de", roles=None
):
    invitation = AdminUnitMemberInvitationAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        email=email,
        roles=roles or ["admin"],
    )
    uow.member_invitations.add(invitation)
    return invitation


def _seed_user(uow, user_id=ACTOR_USER_ID, email="invitee@test.de"):
    uow.users.add(UserAggregate(id=user_id, email=email, locale=None))


class TestInviteUserToOrganizationHandler:
    def test_creates_invitation_and_returns_result(self, uow):
        grant_permission(uow, ADMIN_UNIT_ID, "organization_member_invitations:write")
        cmd = commands.InviteUserToOrganizationCommand.model_construct(
            actor=ACTOR,
            admin_unit_id=ADMIN_UNIT_ID,
            email="invitee@test.de",
            roles=["admin"],
        )

        result = InviteUserToOrganizationHandler().handle(cmd, uow)

        invitation = uow.member_invitations.get(result.id)
        assert invitation.admin_unit_id == ADMIN_UNIT_ID
        assert invitation.email == "invitee@test.de"
        assert invitation.roles == ["admin"]

    def test_unauthorized_actor_raises(self, uow):
        cmd = commands.InviteUserToOrganizationCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de"
        )
        with pytest.raises(UnauthorizedError):
            InviteUserToOrganizationHandler().handle(cmd, uow)


class TestUpdateMemberInvitationHandler:
    def test_updates_roles(self, uow):
        invitation = _seed_invitation(uow, roles=["admin"])
        grant_permission(uow, ADMIN_UNIT_ID, "organization_member_invitations:write")
        cmd = commands.UpdateMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id, roles=["event_verifier"]
        )

        UpdateMemberInvitationHandler().handle(cmd, uow)

        updated = uow.member_invitations.get(invitation.id)
        assert updated.roles == ["event_verifier"]

    def test_not_found_raises(self, uow):
        cmd = commands.UpdateMemberInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            UpdateMemberInvitationHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        invitation = _seed_invitation(uow)
        cmd = commands.UpdateMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            UpdateMemberInvitationHandler().handle(cmd, uow)


class TestRevokeMemberInvitationHandler:
    def test_removes_invitation(self, uow):
        invitation = _seed_invitation(uow)
        grant_permission(uow, ADMIN_UNIT_ID, "organization_member_invitations:write")
        cmd = commands.RevokeMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        RevokeMemberInvitationHandler().handle(cmd, uow)

        assert uow.member_invitations.get(invitation.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.RevokeMemberInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            RevokeMemberInvitationHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        invitation = _seed_invitation(uow)
        cmd = commands.RevokeMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            RevokeMemberInvitationHandler().handle(cmd, uow)


class TestDeclineMemberInvitationHandler:
    def test_removes_invitation(self, uow):
        invitation = _seed_invitation(uow)
        _seed_user(uow)
        cmd = commands.DeclineMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        DeclineMemberInvitationHandler().handle(cmd, uow)

        assert uow.member_invitations.get(invitation.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.DeclineMemberInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            DeclineMemberInvitationHandler().handle(cmd, uow)

    def test_wrong_receiver_raises(self, uow):
        invitation = _seed_invitation(uow, email="someone-else@test.de")
        _seed_user(uow, email="invitee@test.de")
        cmd = commands.DeclineMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            DeclineMemberInvitationHandler().handle(cmd, uow)


class TestAcceptMemberInvitationHandler:
    def test_creates_new_member_with_roles(self, uow):
        invitation = _seed_invitation(uow, roles=["admin"])
        _seed_user(uow)
        cmd = commands.AcceptMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        AcceptMemberInvitationHandler().handle(cmd, uow)

        member = uow.organization_members.get_by_admin_unit_and_user(
            ADMIN_UNIT_ID, ACTOR_USER_ID
        )
        assert member is not None
        assert member.roles == ["admin"]
        assert uow.member_invitations.get(invitation.id) is None

    def test_existing_member_gets_union_of_roles(self, uow):
        invitation = _seed_invitation(uow, roles=["event_verifier"])
        _seed_user(uow)

        existing_member = OrganisationMemberAggregate.create(
            admin_unit_id=ADMIN_UNIT_ID, user_id=ACTOR_USER_ID, roles=["admin"]
        )
        uow.organization_members.add(existing_member)

        cmd = commands.AcceptMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        AcceptMemberInvitationHandler().handle(cmd, uow)

        member = uow.organization_members.get_by_admin_unit_and_user(
            ADMIN_UNIT_ID, ACTOR_USER_ID
        )
        assert member.roles == ["admin", "event_verifier"]

    def test_unknown_role_name_is_kept_on_invitation_but_silently_skipped_by_repo(
        self, uow
    ):
        # The domain layer itself doesn't validate role names (that already
        # happens at form-submit time on the issuer side); silently dropping
        # an unresolvable role name is the infrastructure repository's job
        # (mirroring add_roles_to_admin_unit_member) and is covered by the
        # repository contract tests, not here.
        invitation = _seed_invitation(uow, roles=["wrongrole"])
        _seed_user(uow)
        cmd = commands.AcceptMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        AcceptMemberInvitationHandler().handle(cmd, uow)

        member = uow.organization_members.get_by_admin_unit_and_user(
            ADMIN_UNIT_ID, ACTOR_USER_ID
        )
        assert member.roles == ["wrongrole"]

    def test_not_found_raises(self, uow):
        cmd = commands.AcceptMemberInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            AcceptMemberInvitationHandler().handle(cmd, uow)

    def test_wrong_receiver_raises(self, uow):
        invitation = _seed_invitation(uow, email="someone-else@test.de")
        _seed_user(uow, email="invitee@test.de")
        cmd = commands.AcceptMemberInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            AcceptMemberInvitationHandler().handle(cmd, uow)
