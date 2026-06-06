"""Unit tests for organization deletion command handlers."""

import pytest

from project.application import commands
from project.application.command_handlers.cancel_organization_deletion_handler import (
    CancelOrganizationDeletionHandler,
)
from project.application.command_handlers.request_organization_deletion_handler import (
    RequestOrganizationDeletionHandler,
)
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor

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
    def test_requests_deletion_and_commits(self, uow):
        org = _seed_org(uow)
        cmd = commands.RequestOrganizationDeletionCommand.model_construct(
            actor=Actor(user_id=1), id=org.id
        )

        RequestOrganizationDeletionHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.deletion_requested_at is not None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.RequestOrganizationDeletionCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            RequestOrganizationDeletionHandler().handle(cmd, uow)


# ---------------------------------------------------------------------------
# CancelOrganizationDeletionHandler
# ---------------------------------------------------------------------------


class TestCancelOrganizationDeletionHandler:
    def test_cancels_deletion_and_commits(self, uow):
        org = _seed_org(uow)
        # First request deletion
        org.request_deletion(Actor(user_id=1))
        uow.organizations.update(org)
        assert org.deletion_requested_at is not None

        cmd = commands.CancelOrganizationDeletionCommand.model_construct(
            actor=Actor(user_id=1), id=org.id
        )

        CancelOrganizationDeletionHandler().handle(cmd, uow)

        updated = uow.organizations.get(org.id)
        assert updated.deletion_requested_at is None
        assert uow.committed

    def test_not_found_raises_not_found_error(self, uow):
        cmd = commands.CancelOrganizationDeletionCommand.model_construct(
            actor=Actor(), id=9999
        )

        with pytest.raises(NotFoundError):
            CancelOrganizationDeletionHandler().handle(cmd, uow)
