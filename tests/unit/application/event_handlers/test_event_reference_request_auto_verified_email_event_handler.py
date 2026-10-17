"""Unit tests for EventReferenceRequestAutoVerifiedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.event_reference_request_auto_verified_email_event_handler import (
    EventReferenceRequestAutoVerifiedEmailEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor


class TestEventReferenceRequestAutoVerifiedEmailEventHandler:
    def test_sends_email_to_reviewer_admin_unit_members(self, uow):
        org_service = MagicMock()
        event_read_repo = MagicMock()
        event_read_model = MagicMock()
        event_read_repo.get.return_value = event_read_model

        ref = MagicMock()
        ref.admin_unit_id = 2
        uow.event_references._references_by_event[3] = [ref]

        ev = events.EventReferenceRequestAutoVerified(
            actor=Actor(), id=1, admin_unit_id=2, event_id=3
        )
        EventReferenceRequestAutoVerifiedEmailEventHandler(
            organization_service=org_service, event_read_repo=event_read_repo
        ).handle(ev, uow)

        event_read_repo.get.assert_called_once_with(3)
        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            2,
            "incoming_event_reference_requests:write",
            "reference_auto_verified_notice",
            reference=ref,
            event=event_read_model,
        )

    def test_no_matching_reference_does_not_send_email(self, uow):
        org_service = MagicMock()
        event_read_repo = MagicMock()

        ev = events.EventReferenceRequestAutoVerified(
            actor=Actor(), id=1, admin_unit_id=2, event_id=3
        )
        EventReferenceRequestAutoVerifiedEmailEventHandler(
            organization_service=org_service, event_read_repo=event_read_repo
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_not_called()
