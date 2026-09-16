"""Unit tests for EventReferenceRequestReviewedEmailEventHandler."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

from project.application.event_handlers.event_reference_request_reviewed_email_event_handler import (
    EventReferenceRequestReviewedEmailEventHandler,
)
from project.domain import events
from project.domain.models.aggregates.event_aggregate import EventAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.models.enums.event_status import EventStatus
from project.domain.models.value_objects.event_date_definition_value_object import (
    EventDateDefinitionValueObject,
)


def _make_event(uow, admin_unit_id=99):
    event = EventAggregate.create(
        actor=Actor(),
        admin_unit_id=admin_unit_id,
        name="Referenced Event",
        organizer_id=1,
        event_place_id=1,
        date_definitions=[
            EventDateDefinitionValueObject(start=datetime.now(timezone.utc))
        ],
        status=EventStatus.scheduled,
        public_status=EventPublicStatus.published,
    )
    uow.events.add(event)
    return event


class TestEventReferenceRequestReviewedEmailEventHandler:
    def test_sends_email_to_requester_admin_unit_members(self, uow):
        event = _make_event(uow, admin_unit_id=99)
        org_service = MagicMock()

        ev = events.EventReferenceRequestReviewed(
            actor=Actor(),
            id=1,
            admin_unit_id=2,
            event_id=event.id,
            review_status=EventReferenceRequestReviewStatus.verified,
        )
        EventReferenceRequestReviewedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_called_once_with(
            uow,
            99,
            "outgoing_event_reference_requests:write",
            "reference_request_review_status_notice",
            request=ev,
            requester_admin_unit_id=99,
        )

    def test_missing_event_does_not_send_email(self, uow):
        org_service = MagicMock()

        ev = events.EventReferenceRequestReviewed(
            actor=Actor(),
            id=1,
            admin_unit_id=2,
            event_id=9999,
            review_status=EventReferenceRequestReviewStatus.rejected,
        )
        EventReferenceRequestReviewedEmailEventHandler(
            organization_service=org_service
        ).handle(ev, uow)

        org_service.send_template_mails_to_members_async.assert_not_called()
