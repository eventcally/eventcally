"""Event place created data model."""

from typing import Optional

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.application.webhooks.payloads.nested.payload_image import PayloadImage
from project.application.webhooks.payloads.nested.payload_location import (
    PayloadLocation,
)
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.domain import events


class EventPlaceCreatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    location: Optional[PayloadLocation] = None
    photo: Optional[PayloadImage] = None

    @classmethod
    def from_event(cls, e: events.EventPlaceCreated, ctx: AbstractWebhookMapperContext):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            description=e.description,
            location=PayloadLocation.from_event(e.location, ctx),
            photo=PayloadImage.from_event(e.photo, ctx),
        )
