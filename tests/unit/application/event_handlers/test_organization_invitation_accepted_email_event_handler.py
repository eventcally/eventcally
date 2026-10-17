"""Unit tests for OrganizationInvitationAcceptedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.organization_invitation_accepted_email_event_handler import (
    OrganizationInvitationAcceptedEmailEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor


class TestOrganizationInvitationAcceptedEmailEventHandler:
    def test_sends_email_to_inviting_admin_unit_members(self, uow):
        org_service = MagicMock()

        ev = events.OrganizationInvitationAccepted(
            actor=Actor(),
            id=1,
            inviting_admin_unit_id=2,
            new_admin_unit_id=3,
            new_admin_unit_name="New Org",
            accepting_user_email="invited@test.de",
        )
        OrganizationInvitationAcceptedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            2,
            "organization_invitations:write",
            "organization_invitation_accepted_notice",
            email="invited@test.de",
            new_admin_unit_name="New Org",
            inviting_admin_unit_id=2,
            relation_id=1,
        )
