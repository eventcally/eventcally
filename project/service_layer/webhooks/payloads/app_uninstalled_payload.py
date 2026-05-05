from project.domain import events
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class AppUninstalledPayload(WebhookPayloadBase):
    id: int
    app_id: int
    organization_id: int

    @classmethod
    def from_event(cls, e: events.AppUninstalled, ctx: WebhookMapperContext):
        return cls(
            id=e.id,
            app_id=e.app_id,
            organization_id=e.admin_unit_id,
        )
