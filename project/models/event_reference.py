from sqlalchemy import Column, Integer, UniqueConstraint
from sqlalchemy.event import listens_for

from project import db
from project.models.trackable_mixin import TrackableMixin
from project.utils import make_check_violation


class EventReference(db.Model, TrackableMixin):
    __tablename__ = "eventreference"
    __table_args__ = (UniqueConstraint("event_id", "admin_unit_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    rating = Column(Integer(), default=50)

    def validate(self):
        if self.event and self.event.admin_unit_id == self.admin_unit_id:
            raise make_check_violation("Own events cannot be referenced")


@listens_for(EventReference, "before_insert")
@listens_for(EventReference, "before_update")
def before_saving_event_reference(mapper, connect, self):
    self.validate()
