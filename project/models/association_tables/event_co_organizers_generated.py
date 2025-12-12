from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class EventCoOrganizersGeneratedMixin:
    __tablename__ = "event_coorganizers"
    __table_args__ = (UniqueConstraint("event_id", "organizer_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
    organizer_id = db.Column(
        db.Integer,
        db.ForeignKey("eventorganizer.id", ondelete="CASCADE"),
        nullable=False,
    )
