"""Unit tests for UpdateOrganizationHandler."""

import pytest

from project.application import commands
from project.application.command_handlers.update_organization_handler import (
    UpdateOrganizationHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission


def _make_organization(uow):
    org = OrganizationAggregate.create(
        actor=Actor(), name="Old Name", short_name="old_name"
    )
    uow.organizations.add(org)
    return org


class TestUpdateOrganizationHandler:
    def test_updates_settings_fields(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "settings:write")
        cmd = commands.UpdateOrganizationCommand.model_construct(
            actor=ACTOR,
            id=org.id,
            name="New Name",
            short_name="new_name",
            description="New description",
        )

        UpdateOrganizationHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.name == "New Name"
        assert updated.short_name == "new_name"
        assert updated.description == "New description"

    def test_omitted_fields_left_untouched(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "settings:write")
        cmd = commands.UpdateOrganizationCommand.model_construct(actor=ACTOR, id=org.id)

        UpdateOrganizationHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.name == "Old Name"
        assert updated.short_name == "old_name"

    def test_updates_verification_request_fields(self, uow):
        org = _make_organization(uow)
        grant_permission(uow, org.id, "settings:write")
        cmd = commands.UpdateOrganizationCommand.model_construct(
            actor=ACTOR,
            id=org.id,
            incoming_verification_requests_allowed=True,
            incoming_verification_requests_text="Please verify us",
            incoming_verification_requests_postal_codes=["12345"],
        )

        UpdateOrganizationHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.incoming_verification_requests_allowed is True
        assert updated.incoming_verification_requests_text == "Please verify us"
        assert updated.incoming_verification_requests_postal_codes == ["12345"]

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.UpdateOrganizationCommand.model_construct(actor=ACTOR, id=9999)

        with pytest.raises(NotFoundError):
            UpdateOrganizationHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        org = _make_organization(uow)
        cmd = commands.UpdateOrganizationCommand.model_construct(actor=ACTOR, id=org.id)

        with pytest.raises(UnauthorizedError):
            UpdateOrganizationHandler().handle(cmd, uow)
