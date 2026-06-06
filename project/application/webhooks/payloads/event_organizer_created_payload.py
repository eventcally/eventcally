"""Event organizer created data model."""

from typing import Optional

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.nested.payload_image import PayloadImage
from project.application.webhooks.payloads.nested.payload_location import (
    PayloadLocation,
)
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.domain import events


class EventOrganizerCreatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: str
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    location: Optional[PayloadLocation] = None
    logo: Optional[PayloadImage] = None

    @classmethod
    def from_event(
        cls, e: events.EventOrganizerCreated, ctx: AbstractWebhookMapperContext
    ):
        return cls(
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            email=e.email,
            phone=e.phone,
            fax=e.fax,
            location=PayloadLocation.from_event(e.location, ctx),
            logo=PayloadImage.from_event(e.logo, ctx),
        )
