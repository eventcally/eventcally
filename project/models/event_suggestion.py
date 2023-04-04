from enum import IntEnum

from sqlalchemy import Boolean, Column, Integer, Unicode, UnicodeText
from sqlalchemy.event import listens_for
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.schema import CheckConstraint

from project import db
from project.dbtypes import IntegerEnum
from project.models.event_mixin import EventMixin
from project.models.functions import sanitize_allday_instance
from project.models.trackable_mixin import TrackableMixin


class EventReviewStatus(IntEnum):
    inbox = 1
    verified = 2
    rejected = 3


class EventRejectionReason(IntEnum):
    duplicate = 1
    untrustworthy = 2
    illegal = 3


class EventSuggestion(db.Model, TrackableMixin, EventMixin):
    __tablename__ = "eventsuggestion"
    __table_args__ = (
        CheckConstraint(
            "NOT(event_place_id IS NULL AND event_place_text IS NULL)",
        ),
        CheckConstraint("NOT(organizer_id IS NULL AND organizer_text IS NULL)"),
    )
    id = Column(Integer(), primary_key=True)

    start = db.Column(db.DateTime(timezone=True), nullable=False)
    end = db.Column(db.DateTime(timezone=True), nullable=True)
    allday = db.Column(
        Boolean(),
        nullable=False,
        default=False,
        server_default="0",
    )
    recurrence_rule = Column(UnicodeText())

    review_status = Column(IntegerEnum(EventReviewStatus))
    rejection_resaon = Column(IntegerEnum(EventRejectionReason))

    contact_name = Column(Unicode(255), nullable=False)
    contact_email = Column(Unicode(255))
    contact_phone = Column(Unicode(255))
    contact_email_notice = Column(Boolean())

    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)

    event_place_id = db.Column(
        db.Integer, db.ForeignKey("eventplace.id"), nullable=True
    )
    event_place = db.relationship("EventPlace", uselist=False)
    event_place_text = Column(Unicode(255), nullable=True)

    organizer_id = db.Column(
        db.Integer, db.ForeignKey("eventorganizer.id"), nullable=True
    )
    organizer = db.relationship("EventOrganizer", uselist=False)
    organizer_text = Column(Unicode(255), nullable=True)

    categories = relationship(
        "EventCategory", secondary="eventsuggestion_eventcategories"
    )

    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="SET NULL"), nullable=True
    )
    event = db.relationship("Event", uselist=False)

    @hybrid_property
    def verified(self):
        return self.review_status == EventReviewStatus.verified


@listens_for(EventSuggestion, "before_insert")
@listens_for(EventSuggestion, "before_update")
def purge_event_suggestion(mapper, connect, self):
    if self.organizer_id is not None:
        self.organizer_text = None
    if self.event_place_id is not None:
        self.event_place_text = None
    self.purge_event_mixin()
    sanitize_allday_instance(self)
