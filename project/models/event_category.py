from sqlalchemy import Column, Integer, UniqueConstraint

from project import db
from project.models.custom_event_category_generated import (
    CustomEventCategoryGeneratedMixin,
)
from project.models.custom_event_category_set_generated import (
    CustomEventCategorySetGeneratedMixin,
)
from project.models.event_category_generated import EventCategoryGeneratedMixin


class EventCategory(db.Model, EventCategoryGeneratedMixin):
    pass


class EventEventCategories(db.Model):
    __tablename__ = "event_eventcategories"
    __table_args__ = (UniqueConstraint("event_id", "category_id"),)
    id = Column(Integer(), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("eventcategory.id"), nullable=False
    )


class CustomEventCategorySet(db.Model, CustomEventCategorySetGeneratedMixin):
    pass

    @property
    def label_or_name(self):
        return self.label or self.name

    def __str__(self):  # pragma: no cover
        return self.name or super().__str__()


class CustomEventCategory(db.Model, CustomEventCategoryGeneratedMixin):
    pass

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
