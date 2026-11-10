from __future__ import annotations

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class CalendarEntryAggregate(BaseAggregate):
    id: ObjectId
    calendar_id: ObjectId
    event_id: ObjectId

    @classmethod
    def create(
        cls, actor: Actor, calendar_id: ObjectId, event_id: ObjectId
    ) -> CalendarEntryAggregate:
        return cls(id=-1, calendar_id=calendar_id, event_id=event_id)

    def delete(self, actor: Actor):
        pass
