from sqlalchemy import Column, Integer, Unicode, UniqueConstraint

from project import db
from project.models.trackable_mixin import TrackableMixin


class EventList(db.Model, TrackableMixin):
    __tablename__ = "eventlist"
    __table_args__ = (
        UniqueConstraint(
            "name", "admin_unit_id", name="eventreference_name_admin_unit_id"
        ),
    )
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255))
    admin_unit_id = db.Column(db.Integer, db.ForeignKey("adminunit.id"), nullable=False)


class EventEventLists(db.Model):
    __tablename__ = "event_eventlists"
    __table_args__ = (UniqueConstraint("event_id", "list_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("eventlist.id"), nullable=False)
