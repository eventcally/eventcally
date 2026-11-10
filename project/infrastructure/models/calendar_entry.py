from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.infrastructure.extensions import db
from project.infrastructure.models.calendar_entry_generated import (
    CalendarEntryGeneratedMixin,
)


class CalendarEntry(db.Model, CalendarEntryGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: CalendarEntryAggregate) -> CalendarEntry:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: CalendarEntryAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.calendar_id = aggregate.calendar_id
        self.event_id = aggregate.event_id

    @classmethod
    def to_aggregate(
        cls, model: Optional[CalendarEntry]
    ) -> Optional[CalendarEntryAggregate]:
        if model is None:  # pragma: no cover
            return None

        return CalendarEntryAggregate(
            id=model.id,
            calendar_id=model.calendar_id,
            event_id=model.event_id,
        )
