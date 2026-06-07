from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.extensions import db
from project.models.event import Event
from project.models.event_place_generated import EventPlaceGeneratedMixin
from project.models.image import Image
from project.models.location import Location


class EventPlace(db.Model, EventPlaceGeneratedMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def from_aggregate(cls, aggregate: EventPlaceAggregate) -> EventPlace:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: EventPlaceAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.name = aggregate.name
        self.url = aggregate.url
        self.description = aggregate.description

        if aggregate.location:
            if not self.location:
                self.location = Location()
            self.location.fill_from_value_object(aggregate.location)
        else:
            self.location = None

        if aggregate.photo:
            if not self.photo:
                self.photo = Image()
            self.photo.fill_from_entity(aggregate.photo)
        else:
            self.photo = None

        return self

    @classmethod
    def to_aggregate(cls, model: EventPlace) -> EventPlaceAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = EventPlaceAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            name=model.name,
            url=model.url,
            description=model.description,
            location=model.location.to_value_object() if model.location else None,
            photo=model.photo.to_entity() if model.photo else None,
        )

        return aggregate

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
