from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.models.event_reference_request_generated import (
    EventReferenceRequestGeneratedMixin,
    EventReferenceRequestReviewStatus,
)


class EventReferenceRequest(db.Model, EventReferenceRequestGeneratedMixin):
    @hybrid_property
    def verified(self):
        return self.review_status == EventReferenceRequestReviewStatus.verified


@listens_for(EventReferenceRequest, "before_insert")
@listens_for(EventReferenceRequest, "before_update")
def before_saving_event_reference_request(mapper, connect, self):
    if self.review_status != EventReferenceRequestReviewStatus.rejected:
        self.rejection_reason = None

    if self.rejection_reason == 0:
        self.rejection_reason = None
