from sqlalchemy import Column, Integer, Unicode, UniqueConstraint

from project import db


class EventCategory(db.Model):
    __tablename__ = "eventcategory"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False, unique=True)


class EventEventCategories(db.Model):
    __tablename__ = "event_eventcategories"
    __table_args__ = (UniqueConstraint("event_id", "category_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )
