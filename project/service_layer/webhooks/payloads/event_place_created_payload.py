"""Event place created data model."""

from typing import Optional

from project.domain import events
from project.service_layer.webhooks.payloads.nested.actor import Actor
from project.service_layer.webhooks.payloads.nested.image_created import ImageCreated
from project.service_layer.webhooks.payloads.nested.location_created import (
    LocationCreated,
)
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class EventPlaceCreatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[LocationCreated] = None
    photo: Optional[ImageCreated] = None

    @classmethod
    def from_event(cls, e: events.EventPlaceCreated, ctx: WebhookMapperContext):
        return cls(
            actor=Actor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            description=e.description,
            location=LocationCreated.from_event(e.location, ctx),
            photo=ImageCreated.from_event(e.photo, ctx),
        )
