from __future__ import annotations

from typing import Optional

from project.domain.events.webhook_delivery_created import WebhookDeliveryCreated
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class WebhookDeliveryAggregate(BaseAggregate):
    id: ObjectId
    webhook_event_id: ObjectId
    webhook_id: ObjectId
    app_installation_id: Optional[ObjectId] = None
    app_id: Optional[ObjectId] = None

    @classmethod
    def create(
        cls,
        actor: Actor,
        webhook_event_id: ObjectId,
        webhook_id: ObjectId,
        app_installation_id: Optional[ObjectId] = None,
        app_id: Optional[ObjectId] = None,
    ) -> WebhookDeliveryAggregate:
        instance = cls(
            id=-1,
            webhook_event_id=webhook_event_id,
            webhook_id=webhook_id,
            app_installation_id=app_installation_id,
            app_id=app_id,
        )

        event = WebhookDeliveryCreated(
            actor=actor,
            id=-1,
        )
        instance.domain_events.append(event)

        return instance
