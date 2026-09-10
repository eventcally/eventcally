from __future__ import annotations

from typing import Optional

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import Unsetable


class EventReferenceAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
    rating: Optional[int] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        event_id: ObjectId,
        rating: int = 50,
    ) -> EventReferenceAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            event_id=event_id,
            rating=rating,
        )

        return instance

    def update(
        self,
        actor: Actor,
        rating: Unsetable[int] = unset,
    ):
        self._update_field_with_value("rating", rating)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
