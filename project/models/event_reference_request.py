from enum import IntEnum

from sqlalchemy import Column, Integer, UniqueConstraint
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.dbtypes import IntegerEnum
from project.models.trackable_mixin import TrackableMixin


class EventReferenceRequestReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventReferenceRequestRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3
    irrelevant = 4


class EventReferenceRequest(db.Model, TrackableMixin):
    __tablename__ = "eventreferencerequest"
    __table_args__ = (
        UniqueConstraint(
            "event_id",
            "admin_unit_id",
        ),
    )
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    review_status = Column(IntegerEnum(EventReferenceRequestReviewStatus))
    rejection_reason = Column(IntegerEnum(EventReferenceRequestRejectionReason))

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
