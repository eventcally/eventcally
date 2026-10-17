"""Unit tests for EventReferenceRequestCreatedEmailEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.event_reference_request_created_email_event_handler import (
    EventReferenceRequestCreatedEmailEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor


class TestEventReferenceRequestCreatedEmailEventHandler:
    def test_sends_email_to_reviewer_admin_unit_members(self, uow):
        org_service = MagicMock()
        event_read_repo = MagicMock()
        event_read_model = MagicMock()
        event_read_repo.get.return_value = event_read_model

        ev = events.EventReferenceRequestCreated(
            actor=Actor(), id=1, admin_unit_id=2, event_id=3
        )
        EventReferenceRequestCreatedEmailEventHandler(
            organization_service=org_service, event_read_repo=event_read_repo
        ).handle(ev, uow)

        event_read_repo.get.assert_called_once_with(3)
        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            2,
            "incoming_event_reference_requests:write",
            "reference_request_notice",
            request=ev,
            event=event_read_model,
        )
