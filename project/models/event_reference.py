from sqlalchemy import Column, Integer, UniqueConstraint

from project import db
from project.models.trackable_mixin import TrackableMixin


class EventReference(db.Model, TrackableMixin):
    __tablename__ = "eventreference"
    __table_args__ = (
        UniqueConstraint(
            "event_id", "admin_unit_id", name="eventreference_event_id_admin_unit_id"
        ),
    )
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)
    rating = Column(Integer(), default=50)
