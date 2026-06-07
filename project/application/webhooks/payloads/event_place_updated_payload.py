"""Event place updated data model."""

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
from project.domain.types import ChangedValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class EventPlaceUpdatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    location: Optional[ChangedValue[PayloadLocation]] = OptionalChangedValueField()
    photo: Optional[ChangedValue[PayloadImage]] = OptionalChangedValueField()

    @classmethod
    def from_event(cls, e: events.EventPlaceUpdated, ctx: AbstractWebhookMapperContext):
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
