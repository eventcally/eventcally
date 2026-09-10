from __future__ import annotations

from sqlalchemy.event import listens_for

from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)
from project.extensions import db
from project.models.event_reference_generated import EventReferenceGeneratedMixin
from project.utils import make_check_violation


class EventReference(db.Model, EventReferenceGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: EventReferenceAggregate) -> EventReference:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: EventReferenceAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.event_id = aggregate.event_id
        self.rating = aggregate.rating

    @classmethod
    def to_aggregate(cls, model: EventReference) -> EventReferenceAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = EventReferenceAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            event_id=model.event_id,
            rating=model.rating,
        )

        return aggregate

    def validate(self):
        if self.event and self.event.admin_unit_id == self.admin_unit_id:
            raise make_check_violation(  # pragma: no cover
                "Own events cannot be referenced"
            )


@listens_for(EventReference, "before_insert")
@listens_for(EventReference, "before_update")
def before_saving_event_reference(mapper, connect, self):
    self.validate()
