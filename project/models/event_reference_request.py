from __future__ import annotations

from typing import Optional

from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)
from project.extensions import db
from project.models.event_reference_request_generated import (
    EventReferenceRequestGeneratedMixin,
    EventReferenceRequestReviewStatus,
)


class EventReferenceRequest(db.Model, EventReferenceRequestGeneratedMixin):
    @hybrid_property
    def verified(self):
        return self.review_status == EventReferenceRequestReviewStatus.verified

    @classmethod
    def from_aggregate(
        cls, aggregate: EventReferenceRequestAggregate
    ) -> EventReferenceRequest:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: EventReferenceRequestAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.event_id = aggregate.event_id
        self.review_status = aggregate.review_status
        self.rejection_reason = aggregate.rejection_reason

    @classmethod
    def to_aggregate(
        cls, model: Optional[EventReferenceRequest]
    ) -> Optional[EventReferenceRequestAggregate]:
        if model is None:  # pragma: no cover
            return None

        return EventReferenceRequestAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            event_id=model.event_id,
            review_status=(model.review_status.value if model.review_status else None),
            rejection_reason=(
                model.rejection_reason.value if model.rejection_reason else None
            ),
        )


@listens_for(EventReferenceRequest, "before_insert")
@listens_for(EventReferenceRequest, "before_update")
def before_saving_event_reference_request(mapper, connect, self):
    if self.review_status != EventReferenceRequestReviewStatus.rejected:
        self.rejection_reason = None

    if self.rejection_reason == 0:
        self.rejection_reason = None
