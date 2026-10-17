"""Unit tests for OrganizationInvitationCreatedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.organization_invitation_created_email_event_handler import (
    OrganizationInvitationCreatedEmailEventHandler,
)
from project.domain import events
from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)
from project.domain.models.entities.actor import Actor


class TestOrganizationInvitationCreatedEmailEventHandler:
    def _seed_org(self, uow, name="Inviting Org"):
        org = OrganizationAggregate(id=-1, name=name)
        uow.organizations.add(org)
        return org

    def test_sends_email_when_org_found(self, uow):
        org = self._seed_org(uow)
        email_service = MagicMock()

        ev = events.OrganizationInvitationCreated(
            actor=Actor(), id=1, admin_unit_id=org.id, email="invitee@test.de"
        )
        OrganizationInvitationCreatedEmailEventHandler(
            email_service=email_service
        ).handle(ev, uow)

        email_service.send_template_mail_to_address_async.assert_called_once_with(
            "invitee@test.de",
            "organization_invitation_notice",
            invitation_id=1,
            admin_unit_name="Inviting Org",
        )

    def test_org_not_found_does_not_crash(self, uow):
        email_service = MagicMock()

        ev = events.OrganizationInvitationCreated(
            actor=Actor(), id=1, admin_unit_id=999, email="invitee@test.de"
        )
        OrganizationInvitationCreatedEmailEventHandler(
            email_service=email_service
        ).handle(ev, uow)

        email_service.send_template_mail_to_address_async.assert_not_called()
