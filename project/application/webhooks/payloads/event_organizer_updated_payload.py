"""Event organizer updated data model."""

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
from project.domain.types import OptionalChangedValue
from project.domain.types.changed_value import OptionalChangedOptionalValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)


class EventOrganizerUpdatedPayload(WebhookPayloadBase):
    id: int
    organization_id: int
    name: OptionalChangedValue[str] = OptionalChangedValueField()
    url: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    email: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    phone: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    fax: OptionalChangedOptionalValue[str] = OptionalChangedValueField()
    location: OptionalChangedOptionalValue[PayloadLocation] = (
        OptionalChangedValueField()
    )
    logo: OptionalChangedOptionalValue[PayloadImage] = OptionalChangedValueField()

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
