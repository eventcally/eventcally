from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.domain import events


class AppInstallationDeletedPayload(WebhookPayloadBase):
    id: int
    app_id: int
    organization_id: int

    @classmethod
    def from_event(
        cls, e: events.AppInstallationDeleted, ctx: AbstractWebhookMapperContext
    ):
        return cls(
            id=e.id,
            app_id=e.app_id,
            organization_id=e.admin_unit_id,
        )
