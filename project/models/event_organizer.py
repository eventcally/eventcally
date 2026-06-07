from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.extensions import db
from project.models.association_tables.event_co_organizers_generated import (
    EventCoOrganizersGeneratedMixin,
)
from project.models.event_organizer_generated import EventOrganizerGeneratedMixin
from project.models.image import Image
from project.models.location import Location


class EventOrganizer(db.Model, EventOrganizerGeneratedMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_aggregate(cls, aggregate: EventOrganizerAggregate) -> EventOrganizer:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: EventOrganizerAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.name = aggregate.name
        self.url = aggregate.url
        self.email = aggregate.email
        self.phone = aggregate.phone
        self.fax = aggregate.fax

        if aggregate.location:
            if not self.location:
                self.location = Location()
            self.location.fill_from_value_object(aggregate.location)
        else:
            self.location = None

        if aggregate.logo:
            if not self.logo:
                self.logo = Image()
            self.logo.fill_from_entity(aggregate.logo)
        else:
            self.logo = None

    @classmethod
    def to_aggregate(
        cls, model: Optional[EventOrganizer]
    ) -> Optional[EventOrganizerAggregate]:
        if model is None:  # pragma: no cover
            return None

        aggregate = EventOrganizerAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            name=model.name,
            url=model.url,
            email=model.email,
            phone=model.phone,
            fax=model.fax,
            location=model.location.to_value_object() if model.location else None,
            logo=model.logo.to_entity() if model.logo else None,
        )

        return aggregate

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
