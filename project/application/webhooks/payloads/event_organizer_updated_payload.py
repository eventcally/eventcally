"""Event organizer updated data model."""

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
from project.application.webhooks.payloads.webhook_value_mapping import (
    map_changed_value,
)
from project.domain import events
from project.domain.types import ChangedValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class EventOrganizerUpdatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    email: Optional[ChangedValue[str]] = OptionalChangedValueField()
    phone: Optional[ChangedValue[str]] = OptionalChangedValueField()
    fax: Optional[ChangedValue[str]] = OptionalChangedValueField()
    location: Optional[ChangedValue[PayloadLocation]] = OptionalChangedValueField()
    logo: Optional[ChangedValue[PayloadImage]] = OptionalChangedValueField()

    @classmethod
    def from_event(
        cls, e: events.EventOrganizerUpdated, ctx: AbstractWebhookMapperContext
    ):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            email=e.email,
            phone=e.phone,
            fax=e.fax,
            location=map_changed_value(
                e.location, lambda loc: PayloadLocation.from_event(loc, ctx)
            ),
            logo=map_changed_value(
                e.logo, lambda img: PayloadImage.from_event(img, ctx)
            ),
        )
