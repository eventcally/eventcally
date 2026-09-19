"""Unit tests for AdminUnitInvitation (organization invitation) command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.decline_organization_invitation_handler import (
    DeclineOrganizationInvitationHandler,
)
from project.application.command_handlers.invite_organization_handler import (
    InviteOrganizationHandler,
)
from project.application.command_handlers.revoke_organization_invitation_handler import (
    RevokeOrganizationInvitationHandler,
)
from project.application.command_handlers.update_organization_invitation_handler import (
    UpdateOrganizationInvitationHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission

ADMIN_UNIT_ID = 1
OTHER_USER_ID = 2


def _seed_invitation(uow, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de"):
    invitation = AdminUnitInvitationAggregate.create(
        actor=Actor(), admin_unit_id=admin_unit_id, email=email
    )
    uow.organization_invitations.add(invitation)
    return invitation


def _seed_user(uow, user_id=ACTOR_USER_ID, email="invitee@test.de"):
    uow.users.add(UserAggregate(id=user_id, email=email, locale=None))


class TestInviteOrganizationHandler:
    def test_creates_invitation_and_returns_result(self, uow):
        grant_permission(uow, ADMIN_UNIT_ID, "organization_invitations:write")
        cmd = commands.InviteOrganizationCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de"
        )

        result = InviteOrganizationHandler().handle(cmd, uow)

        assert isinstance(result, commands.InviteOrganizationCommandResult)
        invitation = uow.organization_invitations.get(result.id)
        assert invitation.admin_unit_id == ADMIN_UNIT_ID
        assert invitation.email == "invitee@test.de"

    def test_raises_domain_event(self, uow):
        grant_permission(uow, ADMIN_UNIT_ID, "organization_invitations:write")
        cmd = commands.InviteOrganizationCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de"
        )

        result = InviteOrganizationHandler().handle(cmd, uow)

        invitation = uow.organization_invitations.get(result.id)
        assert len(invitation.domain_events) == 1

    def test_unauthorized_actor_raises(self, uow):
        cmd = commands.InviteOrganizationCommand.model_construct(
            actor=ACTOR, admin_unit_id=ADMIN_UNIT_ID, email="invitee@test.de"
        )

        with pytest.raises(UnauthorizedError):
            InviteOrganizationHandler().handle(cmd, uow)


class TestUpdateOrganizationInvitationHandler:
    def test_updates_invitation(self, uow):
        invitation = _seed_invitation(uow)
        grant_permission(uow, ADMIN_UNIT_ID, "organization_invitations:write")
        cmd = commands.UpdateOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id, admin_unit_name="New Name"
        )

        UpdateOrganizationInvitationHandler().handle(cmd, uow)

        updated = uow.organization_invitations.get(invitation.id)
        assert updated.admin_unit_name == "New Name"

    def test_not_found_raises(self, uow):
        cmd = commands.UpdateOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            UpdateOrganizationInvitationHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        invitation = _seed_invitation(uow)
        cmd = commands.UpdateOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            UpdateOrganizationInvitationHandler().handle(cmd, uow)


class TestRevokeOrganizationInvitationHandler:
    def test_removes_invitation(self, uow):
        invitation = _seed_invitation(uow)
        grant_permission(uow, ADMIN_UNIT_ID, "organization_invitations:write")
        cmd = commands.RevokeOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        RevokeOrganizationInvitationHandler().handle(cmd, uow)

        assert uow.organization_invitations.get(invitation.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.RevokeOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            RevokeOrganizationInvitationHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        invitation = _seed_invitation(uow)
        cmd = commands.RevokeOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            RevokeOrganizationInvitationHandler().handle(cmd, uow)


class TestDeclineOrganizationInvitationHandler:
    def test_removes_invitation(self, uow):
        invitation = _seed_invitation(uow)
        _seed_user(uow)
        cmd = commands.DeclineOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )

        DeclineOrganizationInvitationHandler().handle(cmd, uow)

        assert uow.organization_invitations.get(invitation.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.DeclineOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            DeclineOrganizationInvitationHandler().handle(cmd, uow)

    def test_wrong_receiver_raises(self, uow):
        invitation = _seed_invitation(uow, email="someone-else@test.de")
        _seed_user(uow, email="invitee@test.de")
        cmd = commands.DeclineOrganizationInvitationCommand.model_construct(
            actor=ACTOR, id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            DeclineOrganizationInvitationHandler().handle(cmd, uow)

    def test_unknown_actor_user_raises(self, uow):
        invitation = _seed_invitation(uow)
        cmd = commands.DeclineOrganizationInvitationCommand.model_construct(
            actor=Actor(user_id=OTHER_USER_ID), id=invitation.id
        )
        with pytest.raises(UnauthorizedError):
            DeclineOrganizationInvitationHandler().handle(cmd, uow)
