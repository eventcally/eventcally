from sqlalchemy import Column, Integer, UniqueConstraint

from project import db
from project.models.event_list_generated import EventListGeneratedMixin


class EventList(db.Model, EventListGeneratedMixin):
    pass


class EventEventLists(db.Model):
    __tablename__ = "event_eventlists"
    __table_args__ = (UniqueConstraint("event_id", "list_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    list_id = db.Column(db.Integer, db.ForeignKey("eventlist.id"), nullable=False)
