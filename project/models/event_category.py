from sqlalchemy import Column, Integer, Unicode, UniqueConstraint
from sqlalchemy.orm import backref, relationship

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


class CustomEventCategorySet(db.Model):
    __tablename__ = "customeventcategoryset"
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    label = Column(Unicode(255), nullable=True)
    categories = relationship(
        "CustomEventCategory",
        cascade="all, delete-orphan",
        backref=backref("category_set", lazy=True),
    )

    @property
    def label_or_name(self):
        return self.label or self.name

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class CustomEventCategory(db.Model):
    __tablename__ = "customeventcategory"
    __table_args__ = (UniqueConstraint("name", "category_set_id"),)
    id = Column(Integer(), primary_key=True)
    name = Column(Unicode(255), nullable=False)
    label = Column(Unicode(255), nullable=True)
    category_set_id = db.Column(
        db.Integer,
        db.ForeignKey("customeventcategoryset.id", ondelete="CASCADE"),
        nullable=False,
    )

    @property
    def label_or_name(self):
        return self.label or self.name

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class EventCustomEventCategories(db.Model):
    __tablename__ = "event_customeventcategories"
    __table_args__ = (UniqueConstraint("event_id", "category_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("customeventcategory.id"), nullable=False
    )
