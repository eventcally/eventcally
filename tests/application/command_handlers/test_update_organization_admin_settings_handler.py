"""Unit tests for UpdateOrganizationAdminSettingsHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_organization_admin_settings_handler import (
    UpdateOrganizationAdminSettingsHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.aggregates.user_aggregate import UserAggregate
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, ACTOR_USER_ID, grant_permission


def _make_organization(uow):
    org = OrganizationAggregate.create(
        actor=Actor(), name="Old Name", short_name="old_name"
    )
    uow.organizations.add(org)
    return org


def _make_platform_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


class TestUpdateOrganizationAdminSettingsHandler:
    def test_updates_admin_settings_fields(self, uow):
        org = _make_organization(uow)
        _make_platform_admin(uow)
        cmd = commands.UpdateOrganizationAdminSettingsCommand.model_construct(
            actor=ACTOR,
            id=org.id,
            incoming_reference_requests_allowed=True,
            can_create_other=True,
            can_invite_other=True,
            can_verify_other=True,
        )

        UpdateOrganizationAdminSettingsHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.incoming_reference_requests_allowed is True
        assert updated.can_create_other is True
        assert updated.can_invite_other is True
        assert updated.can_verify_other is True

    def test_not_found_raises(self, uow):
        _make_platform_admin(uow)
        cmd = commands.UpdateOrganizationAdminSettingsCommand.model_construct(
            actor=ACTOR, id=9999
        )

        with pytest.raises(NotFoundError):
            UpdateOrganizationAdminSettingsHandler().handle(cmd, uow)

    def test_non_platform_admin_actor_raises(self, uow):
        org = _make_organization(uow)
        cmd = commands.UpdateOrganizationAdminSettingsCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        with pytest.raises(UnauthorizedError):
            UpdateOrganizationAdminSettingsHandler().handle(cmd, uow)

    def test_org_member_with_settings_write_but_not_platform_admin_raises(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "settings:write")
        cmd = commands.UpdateOrganizationAdminSettingsCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        with pytest.raises(UnauthorizedError):
            UpdateOrganizationAdminSettingsHandler().handle(cmd, uow)
