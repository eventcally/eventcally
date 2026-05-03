"""Event place updated data model."""

from typing import Optional

from project.domain import events
from project.domain.types import ChangedValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import Unsetable
from project.service_layer.webhooks.payloads.nested.actor import Actor
from project.service_layer.webhooks.payloads.nested.image_updated import ImageUpdated
from project.service_layer.webhooks.payloads.nested.location_updated import (
    LocationUpdated,
)
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class EventPlaceUpdatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: Optional[ChangedValue[str]] = OptionalChangedValueField()
    url: Optional[ChangedValue[str]] = OptionalChangedValueField()
    description: Optional[ChangedValue[str]] = OptionalChangedValueField()
    location: Unsetable[LocationUpdated] = UnsetField()
    photo: Unsetable[ImageUpdated] = UnsetField()

    @classmethod
    def from_event(cls, e: events.EventPlaceUpdated, ctx: WebhookMapperContext):
        return cls(
            actor=Actor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
            name=e.name,
            url=e.url,
            description=e.description,
            location=LocationUpdated.from_event(e.location, ctx),
            photo=ImageUpdated.from_event(e.photo, ctx),
        )
