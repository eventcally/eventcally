from project import db
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint


class EventCustomEventCategoriesGeneratedMixin:
    __tablename__ = "event_customeventcategories"
    __table_args__ = (UniqueConstraint("category_id", "event_id"),)
    id = Column(Integer(), primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("customeventcategory.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id = db.Column(
        db.Integer, db.ForeignKey("event.id", ondelete="CASCADE"), nullable=False
    )
