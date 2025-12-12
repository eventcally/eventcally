from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project import db
from project.models.association_tables.event_co_organizers_generated import (
    EventCoOrganizersGeneratedMixin,
)
from project.models.event_organizer_generated import EventOrganizerGeneratedMixin


class EventOrganizer(db.Model, EventOrganizerGeneratedMixin):
    @hybrid_property
    def number_of_events(self):
        return len(self.events)

    @number_of_events.expression
    def number_of_events(cls):
        from project.models.event import Event

        return (
            select(func.count()).where(Event.organizer_id == cls.id).scalar_subquery()
        )

    def __str__(self):
        return self.name or super().__str__()


class EventCoOrganizers(db.Model, EventCoOrganizersGeneratedMixin):
    pass
