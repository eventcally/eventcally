"""Unit tests for UpdateUserRolesHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_user_roles_handler import (
    UpdateUserRolesHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission

TARGET_USER_ID = 42


def _make_actor_as_platform_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


def _make_target_user(uow, id=TARGET_USER_ID, **kwargs):
    user = UserAggregate(id=id, email="target@test.de", locale=None, **kwargs)
    uow.users.add(user)
    return user


class TestUpdateUserRolesHandler:
    def test_updates_roles(self, uow):
        _make_actor_as_platform_admin(uow)
        _make_target_user(uow)
        cmd = commands.UpdateUserRolesCommand.model_construct(
            actor=ACTOR, id=TARGET_USER_ID, roles=["admin"]
        )

        UpdateUserRolesHandler().handle(cmd, uow)

        updated = uow.users.get(TARGET_USER_ID)
        assert updated.roles == ["admin"]

    def test_not_found_raises(self, uow):
        _make_actor_as_platform_admin(uow)
        cmd = commands.UpdateUserRolesCommand.model_construct(
            actor=ACTOR, id=9999, roles=["admin"]
        )

        with pytest.raises(NotFoundError):
            UpdateUserRolesHandler().handle(cmd, uow)

    def test_non_platform_admin_actor_raises(self, uow):
        _make_target_user(uow)
        cmd = commands.UpdateUserRolesCommand.model_construct(
            actor=ACTOR, id=TARGET_USER_ID, roles=["admin"]
        )

        with pytest.raises(UnauthorizedError):
            UpdateUserRolesHandler().handle(cmd, uow)

    def test_org_member_with_settings_write_but_not_platform_admin_raises(self, uow):
        _make_target_user(uow)
        grant_permission(uow, 1, "settings:write")
        cmd = commands.UpdateUserRolesCommand.model_construct(
            actor=ACTOR, id=TARGET_USER_ID, roles=["admin"]
        )

        with pytest.raises(UnauthorizedError):
            UpdateUserRolesHandler().handle(cmd, uow)
