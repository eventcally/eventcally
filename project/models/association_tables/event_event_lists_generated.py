from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class EventEventListsGeneratedMixin:
    __tablename__ = "event_eventlists"
    __table_args__ = (UniqueConstraint("list_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    list_id = db.Column(
        db.Integer, db.ForeignKey("eventlist.id", ondelete="CASCADE"), nullable=False
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
