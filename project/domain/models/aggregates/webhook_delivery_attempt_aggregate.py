from __future__ import annotations

import datetime
from typing import Optional

from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class WebhookDeliveryAttemptAggregate(BaseAggregate):
    id: ObjectId
    url: str
    start_at: datetime.datetime
    end_at: datetime.datetime
    webhook_delivery_id: ObjectId
    status: Optional[str] = None
    status_code: Optional[str] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        url: str,
        start_at: datetime.datetime,
        end_at: datetime.datetime,
        webhook_delivery_id: ObjectId,
        status: Optional[str] = None,
        status_code: Optional[str] = None,
    ) -> WebhookDeliveryAttemptAggregate:
        instance = cls(
            id=-1,
            url=url,
            start_at=start_at,
            end_at=end_at,
            webhook_delivery_id=webhook_delivery_id,
            status=status,
            status_code=status_code,
        )
        return instance
