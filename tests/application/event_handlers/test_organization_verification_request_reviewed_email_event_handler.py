"""Unit tests for OrganizationVerificationRequestReviewedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.organization_verification_request_reviewed_email_event_handler import (
    OrganizationVerificationRequestReviewedEmailEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)


class TestOrganizationVerificationRequestReviewedEmailEventHandler:
    def test_sends_email_to_source_admin_unit_members(self, uow):
        org_service = MagicMock()

        ev = events.OrganizationVerificationRequestReviewed(
            actor=Actor(),
            id=1,
            source_admin_unit_id=2,
            target_admin_unit_id=3,
            review_status=OrganizationVerificationRequestReviewStatus.verified,
        )
        OrganizationVerificationRequestReviewedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            2,
            "outgoing_organization_verification_requests:write",
            "verification_request_review_status_notice",
            request=ev,
        )
