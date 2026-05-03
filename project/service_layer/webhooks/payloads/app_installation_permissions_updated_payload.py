from project.domain import events
from project.service_layer.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext


class AppInstallationPermissionsUpdatedPayload(WebhookPayloadBase):
    id: int
    app_id: int
    organization_id: int
    permissions: list[str]

    @classmethod
    def from_event(
        cls,
        e: events.AppInstallationPermissionsUpdated,
        ctx: WebhookMapperContext,
    ):
        return cls(
            id=e.id,
            app_id=e.app_id,
            organization_id=e.admin_unit_id,
            permissions=e.permissions,
        )
