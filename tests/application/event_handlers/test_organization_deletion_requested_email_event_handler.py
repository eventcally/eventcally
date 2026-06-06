"""Unit tests for OrganizationDeletionRequestedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.organization_deletion_requested_email_event_handler import (
    OrganizationDeletionRequestedEmailEventHandler,
)
from project.domain import events
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor


class TestOrganizationDeletionRequestedEmailEventHandler:
    def _seed_org(self, uow):
        org = OrganizationAggregate(id=-1)
        uow.organizations.add(org)
        return org

    def test_sends_email_when_org_found(self, uow):
        org = self._seed_org(uow)
        org_service = MagicMock()

        ev = events.OrganizationDeletionRequested(actor=Actor(), id=org.id)
        OrganizationDeletionRequestedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            org.id,
            "settings:write",
            "organization_deletion_requested_notice",
            admin_unit=org,
        )

    def test_org_not_found_does_not_crash(self, uow):
        """When org is not found, handler should return early without error."""
        org_service = MagicMock()

        ev = events.OrganizationDeletionRequested(actor=Actor(), id=9999)
        OrganizationDeletionRequestedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_not_called()
