from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.models.event import Event
from project.models.event_place_generated import EventPlaceGeneratedMixin


class EventPlace(db.Model, EventPlaceGeneratedMixin):
    @hybrid_property
    def number_of_events(self):
        return len(self.events)

    @number_of_events.expression
    def number_of_events(cls):
        return (
            select(func.count()).where(Event.event_place_id == cls.id).scalar_subquery()
        )

    def __str__(self):
        return self.name or super().__str__()
