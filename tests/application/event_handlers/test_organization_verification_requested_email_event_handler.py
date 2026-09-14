"""Unit tests for OrganizationVerificationRequestedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.organization_verification_requested_email_event_handler import (
    OrganizationVerificationRequestedEmailEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor


class TestOrganizationVerificationRequestedEmailEventHandler:
    def test_sends_email_to_target_admin_unit_members(self, uow):
        org_service = MagicMock()

        ev = events.OrganizationVerificationRequested(
            actor=Actor(), id=1, source_admin_unit_id=2, target_admin_unit_id=3
        )
        OrganizationVerificationRequestedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            3,
            "incoming_organization_verification_requests:write",
            "verification_request_notice",
            request=ev,
        )
