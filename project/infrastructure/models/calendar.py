from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.infrastructure.extensions import db
from project.infrastructure.models.calendar_generated import CalendarGeneratedMixin


class Calendar(db.Model, CalendarGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: CalendarAggregate) -> Calendar:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: CalendarAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.admin_unit_id = aggregate.admin_unit_id
        self.name = aggregate.name
        self.description = aggregate.description
        self.private = aggregate.private

    @classmethod
    def to_aggregate(cls, model: Optional[Calendar]) -> Optional[CalendarAggregate]:
        if model is None:  # pragma: no cover
            return None

        return CalendarAggregate(
            id=model.id,
            admin_unit_id=model.admin_unit_id,
            name=model.name,
            description=model.description,
            private=model.private,
        )
