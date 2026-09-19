"""Unit tests for UpdateSettingsHandler and UpdatePlanningSettingsHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_planning_settings_handler import (
    UpdatePlanningSettingsHandler,
)
from project.application.command_handlers.update_settings_handler import (
    UpdateSettingsHandler,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.aggregates.settings_aggregate import SettingsAggregate
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission


def _make_actor_as_platform_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


class TestUpdateSettingsHandler:
    def test_creates_settings_when_absent(self, uow):
        _make_actor_as_platform_admin(uow)
        cmd = commands.UpdateSettingsCommand.model_construct(
            actor=ACTOR, tos="Terms", legal_notice="Legal"
        )

        UpdateSettingsHandler().handle(cmd, uow)

        settings = uow.settings.get()
        assert settings is not None
        assert settings.tos == "Terms"
        assert settings.legal_notice == "Legal"

    def test_updates_existing_settings(self, uow):
        _make_actor_as_platform_admin(uow)
        existing = SettingsAggregate.create(actor=ACTOR)
        uow.settings.add(existing)

        cmd = commands.UpdateSettingsCommand.model_construct(actor=ACTOR, contact="Us")

        UpdateSettingsHandler().handle(cmd, uow)

        settings = uow.settings.get()
        assert settings.contact == "Us"

    def test_non_platform_admin_actor_raises(self, uow):
        cmd = commands.UpdateSettingsCommand.model_construct(actor=ACTOR, tos="Terms")

        with pytest.raises(UnauthorizedError):
            UpdateSettingsHandler().handle(cmd, uow)

    def test_org_member_with_settings_write_but_not_platform_admin_raises(self, uow):
        grant_permission(uow, 1, "settings:write")
        cmd = commands.UpdateSettingsCommand.model_construct(actor=ACTOR, tos="Terms")

        with pytest.raises(UnauthorizedError):
            UpdateSettingsHandler().handle(cmd, uow)


class TestUpdatePlanningSettingsHandler:
    def test_creates_settings_when_absent(self, uow):
        _make_actor_as_platform_admin(uow)
        cmd = commands.UpdatePlanningSettingsCommand.model_construct(
            actor=ACTOR, planning_external_calendars="[]"
        )

        UpdatePlanningSettingsHandler().handle(cmd, uow)

        settings = uow.settings.get()
        assert settings is not None
        assert settings.planning_external_calendars == "[]"

    def test_updates_existing_settings(self, uow):
        _make_actor_as_platform_admin(uow)
        existing = SettingsAggregate.create(actor=ACTOR)
        uow.settings.add(existing)

        cmd = commands.UpdatePlanningSettingsCommand.model_construct(
            actor=ACTOR, planning_external_calendars='[{"url": "x"}]'
        )

        UpdatePlanningSettingsHandler().handle(cmd, uow)

        settings = uow.settings.get()
        assert settings.planning_external_calendars == '[{"url": "x"}]'

    def test_non_platform_admin_actor_raises(self, uow):
        cmd = commands.UpdatePlanningSettingsCommand.model_construct(
            actor=ACTOR, planning_external_calendars="[]"
        )

        with pytest.raises(UnauthorizedError):
            UpdatePlanningSettingsHandler().handle(cmd, uow)

    def test_org_member_with_settings_write_but_not_platform_admin_raises(self, uow):
        grant_permission(uow, 1, "settings:write")
        cmd = commands.UpdatePlanningSettingsCommand.model_construct(
            actor=ACTOR, planning_external_calendars="[]"
        )

        with pytest.raises(UnauthorizedError):
            UpdatePlanningSettingsHandler().handle(cmd, uow)
