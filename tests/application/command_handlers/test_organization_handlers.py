"""Unit tests for organization deletion command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.cancel_organization_deletion_handler import (
    CancelOrganizationDeletionHandler,
)
from project.application.command_handlers.request_organization_deletion_handler import (
    RequestOrganizationDeletionHandler,
)
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor
from tests.application.conftest import ACTOR, grant_permission

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_org(uow):
    org = OrganizationAggregate(id=-1)
    uow.organizations.add(org)
    return org


# ---------------------------------------------------------------------------
# RequestOrganizationDeletionHandler
# ---------------------------------------------------------------------------


class TestRequestOrganizationDeletionHandler:
    def test_requests_deletion(self, uow):
        org = _seed_org(uow)
        grant_permission(uow, org.id, "settings:write")
        cmd = commands.RequestOrganizationDeletionCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        RequestOrganizationDeletionHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.deletion_requested_at is not None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.RequestOrganizationDeletionCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            RequestOrganizationDeletionHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        org = _seed_org(uow)
        cmd = commands.RequestOrganizationDeletionCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        with pytest.raises(UnauthorizedError):
            RequestOrganizationDeletionHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# CancelOrganizationDeletionHandler
# ---------------------------------------------------------------------------


class TestCancelOrganizationDeletionHandler:
    def test_cancels_deletion(self, uow):
        org = _seed_org(uow)
        # First request deletion
        org.request_deletion(Actor(user_id=1))
        uow.organizations.update(org)
        assert org.deletion_requested_at is not None
        grant_permission(uow, org.id, "settings:write")

        cmd = commands.CancelOrganizationDeletionCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        CancelOrganizationDeletionHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.deletion_requested_at is None

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.CancelOrganizationDeletionCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            CancelOrganizationDeletionHandler().handle(cmd, uow)

    def test_actor_without_permission_raises_unauthorized_error(self, uow):
        org = _seed_org(uow)
        org.request_deletion(Actor(user_id=1))
        uow.organizations.update(org)

        cmd = commands.CancelOrganizationDeletionCommand.model_construct(
            actor=ACTOR, id=org.id
        )

        with pytest.raises(UnauthorizedError):
            CancelOrganizationDeletionHandler().handle(cmd, uow)
