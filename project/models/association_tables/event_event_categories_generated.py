from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class EventEventCategoriesGeneratedMixin:
    __tablename__ = "event_eventcategories"
    __table_args__ = (UniqueConstraint("category_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("eventcategory.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
