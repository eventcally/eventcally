"""Event organizer created data model."""

from typing import Optional

from project.domain import events
from project.service_layer.webhooks.payloads.nested.image_created import ImageCreated
from project.service_layer.webhooks.payloads.nested.location_created import (
    LocationCreated,
)
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class EventOrganizerCreatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[LocationCreated] = None
    logo: Optional[ImageCreated] = None

    @classmethod
    def from_event(cls, e: events.EventOrganizerCreated, ctx: WebhookMapperContext):
        return cls(
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            email=e.email,
            phone=e.phone,
            fax=e.fax,
            location=LocationCreated.from_event(e.location, ctx),
            logo=ImageCreated.from_event(e.logo, ctx),
        )
