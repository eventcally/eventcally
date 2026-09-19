"""Unit tests for OrganizationMember command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.change_organization_member_roles_handler import (
    ChangeOrganizationMemberRolesHandler,
)
from project.application.command_handlers.leave_organization_handler import (
    LeaveOrganizationHandler,
)
from project.application.command_handlers.remove_organization_member_handler import (
    RemoveOrganizationMemberHandler,
)
from project.domain.errors import ConstraintError, NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission

ADMIN_UNIT_ID = 1
OTHER_USER_ID = 2


def _seed_member(uow, admin_unit_id=ADMIN_UNIT_ID, user_id=ACTOR_USER_ID, roles=None):
    member = OrganisationMemberAggregate.create(
        admin_unit_id=admin_unit_id, user_id=user_id, roles=roles or ["admin"]
    )
    uow.organization_members.add(member)
    return member


def _seed_user(uow, user_id=ACTOR_USER_ID, is_platform_admin=False):
    uow.users.add(
        UserAggregate(
            id=user_id,
            email="user@test.de",
            locale=None,
            is_platform_admin=is_platform_admin,
        )
    )


class TestChangeOrganizationMemberRolesHandler:
    def test_updates_roles_for_other_member(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID, roles=["event_verifier"])
        grant_permission(uow, ADMIN_UNIT_ID, "organization_members:write")
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=member.id, roles=["admin"]
        )

        ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

        updated = uow.organization_members.get(member.id)
        assert updated.roles == ["admin"]

    def test_not_found_raises(self, uow):
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=999, roles=["admin"]
        )
        with pytest.raises(NotFoundError):
            ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID, roles=["event_verifier"])
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=member.id, roles=["admin"]
        )
        with pytest.raises(UnauthorizedError):
            ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

    def test_self_edit_forces_admin_when_not_platform_admin(self, uow):
        member = _seed_member(uow, user_id=ACTOR_USER_ID, roles=["admin"])
        grant_permission(uow, ADMIN_UNIT_ID, "organization_members:write")
        _seed_user(uow, is_platform_admin=False)
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=member.id, roles=["event_verifier"]
        )

        ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

        updated = uow.organization_members.get(member.id)
        assert "admin" in updated.roles
        assert "event_verifier" in updated.roles

    def test_self_edit_platform_admin_can_remove_own_admin_role(self, uow):
        member = _seed_member(uow, user_id=ACTOR_USER_ID, roles=["admin"])
        grant_permission(uow, ADMIN_UNIT_ID, "organization_members:write")
        _seed_user(uow, is_platform_admin=True)
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=member.id, roles=["event_verifier"]
        )

        ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

        updated = uow.organization_members.get(member.id)
        assert updated.roles == ["event_verifier"]

    def test_editing_someone_else_does_not_force_admin(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID, roles=["admin"])
        grant_permission(uow, ADMIN_UNIT_ID, "organization_members:write")
        cmd = commands.ChangeOrganizationMemberRolesCommand.model_construct(
            actor=ACTOR, id=member.id, roles=["event_verifier"]
        )

        ChangeOrganizationMemberRolesHandler().handle(cmd, uow)

        updated = uow.organization_members.get(member.id)
        assert updated.roles == ["event_verifier"]


class TestRemoveOrganizationMemberHandler:
    def test_removes_member(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID)
        grant_permission(uow, ADMIN_UNIT_ID, "organization_members:write")
        cmd = commands.RemoveOrganizationMemberCommand.model_construct(
            actor=ACTOR, id=member.id
        )

        RemoveOrganizationMemberHandler().handle(cmd, uow)

        assert uow.organization_members.get(member.id) is None

    def test_not_found_raises(self, uow):
        cmd = commands.RemoveOrganizationMemberCommand.model_construct(
            actor=ACTOR, id=999
        )
        with pytest.raises(NotFoundError):
            RemoveOrganizationMemberHandler().handle(cmd, uow)

    def test_unauthorized_actor_raises(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID)
        cmd = commands.RemoveOrganizationMemberCommand.model_construct(
            actor=ACTOR, id=member.id
        )
        with pytest.raises(UnauthorizedError):
            RemoveOrganizationMemberHandler().handle(cmd, uow)


class TestLeaveOrganizationHandler:
    def test_leaves_when_another_admin_exists(self, uow):
        member = _seed_member(uow, user_id=ACTOR_USER_ID)
        grant_permission(
            uow, ADMIN_UNIT_ID, "organization_members:write", user_id=OTHER_USER_ID
        )
        _seed_user(uow, is_platform_admin=False)
        cmd = commands.LeaveOrganizationCommand.model_construct(
            actor=ACTOR, id=member.id
        )

        LeaveOrganizationHandler().handle(cmd, uow)

        assert uow.organization_members.get(member.id) is None

    def test_platform_admin_bypasses_last_admin_check(self, uow):
        member = _seed_member(uow, user_id=ACTOR_USER_ID)
        _seed_user(uow, is_platform_admin=True)
        cmd = commands.LeaveOrganizationCommand.model_construct(
            actor=ACTOR, id=member.id
        )

        LeaveOrganizationHandler().handle(cmd, uow)

        assert uow.organization_members.get(member.id) is None

    def test_last_admin_raises_constraint_error(self, uow):
        member = _seed_member(uow, user_id=ACTOR_USER_ID)
        _seed_user(uow, is_platform_admin=False)
        cmd = commands.LeaveOrganizationCommand.model_construct(
            actor=ACTOR, id=member.id
        )

        with pytest.raises(ConstraintError):
            LeaveOrganizationHandler().handle(cmd, uow)

        assert uow.organization_members.get(member.id) is not None

    def test_wrong_user_raises_unauthorized(self, uow):
        member = _seed_member(uow, user_id=OTHER_USER_ID)
        cmd = commands.LeaveOrganizationCommand.model_construct(
            actor=ACTOR, id=member.id
        )
        with pytest.raises(UnauthorizedError):
            LeaveOrganizationHandler().handle(cmd, uow)

    def test_not_found_raises(self, uow):
        cmd = commands.LeaveOrganizationCommand.model_construct(actor=ACTOR, id=999)
        with pytest.raises(NotFoundError):
            LeaveOrganizationHandler().handle(cmd, uow)
