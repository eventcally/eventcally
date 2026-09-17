"""Unit tests for ResetTosAcceptedForUsersHandler."""

import datetime

import pytest

from project.application import commands
from project.application.command_handlers.reset_tos_accepted_for_users_handler import (
    ResetTosAcceptedForUsersHandler,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission


def _make_actor_as_platform_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


class TestResetTosAcceptedForUsersHandler:
    def test_resets_tos_accepted_for_all_users(self, uow):
        _make_actor_as_platform_admin(uow)
        other_user = UserAggregate(
            id=99,
            email="other@test.de",
            locale=None,
            tos_accepted_at=datetime.datetime.now(datetime.UTC),
        )
        uow.users.add(other_user)

        cmd = commands.ResetTosAcceptedForUsersCommand.model_construct(actor=ACTOR)

        result = ResetTosAcceptedForUsersHandler().handle(cmd, uow)

        assert result == 1
        assert uow.users.get(99).tos_accepted_at is None

    def test_non_platform_admin_actor_raises(self, uow):
        cmd = commands.ResetTosAcceptedForUsersCommand.model_construct(actor=ACTOR)

        with pytest.raises(UnauthorizedError):
            ResetTosAcceptedForUsersHandler().handle(cmd, uow)

    def test_org_member_with_settings_write_but_not_platform_admin_raises(self, uow):
        grant_permission(uow, 1, "settings:write")
        cmd = commands.ResetTosAcceptedForUsersCommand.model_construct(actor=ACTOR)

        with pytest.raises(UnauthorizedError):
            ResetTosAcceptedForUsersHandler().handle(cmd, uow)
