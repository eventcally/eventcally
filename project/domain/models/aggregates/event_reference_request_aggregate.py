from __future__ import annotations

from typing import Optional

from project.domain.errors import ConstraintError
from project.domain.events.event_reference_request_auto_verified import (
    EventReferenceRequestAutoVerified,
)
from project.domain.events.event_reference_request_created import (
    EventReferenceRequestCreated,
)
from project.domain.events.event_reference_request_reviewed import (
    EventReferenceRequestReviewed,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId


class EventReferenceRequestAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
    review_status: EventReferenceRequestReviewStatus = (
        EventReferenceRequestReviewStatus.inbox
    )
    rejection_reason: Optional[EventReferenceRequestRejectionReason] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        event_id: ObjectId,
        auto_verified: bool = False,
    ) -> EventReferenceRequestAggregate:
        review_status = (
            EventReferenceRequestReviewStatus.verified
            if auto_verified
            else EventReferenceRequestReviewStatus.inbox
        )

        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            event_id=event_id,
            review_status=review_status,
        )

        if auto_verified:
            event = EventReferenceRequestAutoVerified(
                actor=actor,
                id=-1,
                admin_unit_id=admin_unit_id,
                event_id=event_id,
            )
        else:
            event = EventReferenceRequestCreated(
                actor=actor,
                id=-1,
                admin_unit_id=admin_unit_id,
                event_id=event_id,
            )
        instance.domain_events.append(event)

        return instance

    def _ensure_not_yet_verified(self):
        if self.review_status == EventReferenceRequestReviewStatus.verified:
            raise ConstraintError("Reference request already verified.")

    def verify(self, actor: Actor):
        self._ensure_not_yet_verified()

        self.review_status = EventReferenceRequestReviewStatus.verified
        self.rejection_reason = None

        self.domain_events.append(
            EventReferenceRequestReviewed(
                actor=actor,
                id=self.id,
                admin_unit_id=self.admin_unit_id,
                event_id=self.event_id,
                review_status=self.review_status,
            )
        )

    def reject(
        self,
        actor: Actor,
        rejection_reason: Optional[EventReferenceRequestRejectionReason] = None,
    ):
        self._ensure_not_yet_verified()

        self.review_status = EventReferenceRequestReviewStatus.rejected
        self.rejection_reason = rejection_reason

        self.domain_events.append(
            EventReferenceRequestReviewed(
                actor=actor,
                id=self.id,
                admin_unit_id=self.admin_unit_id,
                event_id=self.event_id,
                review_status=self.review_status,
            )
        )

    def delete(self, actor: Actor):
        pass
