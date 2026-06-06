from __future__ import annotations

import datetime

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class WebhookEventAggregate(BaseAggregate):
    id: ObjectId
    timestamp: datetime.datetime
    event_type: str
    payload: dict

    @classmethod
    def create(
        cls,
        actor: Actor,
        timestamp: datetime.datetime,
        event_type: str,
        payload: dict,
    ) -> WebhookEventAggregate:
        instance = cls(
            id=-1,
            event_type=event_type,
            timestamp=timestamp,
            payload=payload,
        )
        return instance
