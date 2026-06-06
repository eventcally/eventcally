"""Event place deleted data model."""

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.domain import events


class EventPlaceDeletedPayload(WebhookPayloadBase):
    id: int
    organization_id: int

    @classmethod
    def from_event(cls, e: events.EventPlaceDeleted, ctx: AbstractWebhookMapperContext):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
        )
