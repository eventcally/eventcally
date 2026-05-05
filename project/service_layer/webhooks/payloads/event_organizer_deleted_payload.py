"""Event organizer deleted data model."""

from project.domain import events
from project.service_layer.webhooks.payloads.nested.actor import Actor
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class EventOrganizerDeletedPayload(WebhookPayloadBase):
    id: int
    organization_id: int

    @classmethod
    def from_event(cls, e: events.EventOrganizerDeleted, ctx: WebhookMapperContext):
        return cls(
            actor=Actor.from_event(e.actor, ctx),
            id=e.id,
            organization_id=e.admin_unit_id,
        )
