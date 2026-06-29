from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.application.webhooks.payloads.webhook_payload_base import (
    WebhookPayloadBase,
)
from project.domain import events
from project.domain.types import ObjectId
from project.domain.types.changed_value import ChangedValue


class AppInstallationPermissionsUpdatedPayload(WebhookPayloadBase):
    id: ObjectId
    app_id: ObjectId
    organization_id: ObjectId
    permissions: ChangedValue[set[str]]

    @classmethod
    def from_event(
        cls,
        e: events.AppInstallationPermissionsUpdated,
        ctx: AbstractWebhookMapperContext,
    ):
        return cls(
            actor=PayloadActor.from_event(e.actor, ctx),
            id=e.id,
            app_id=e.app_id,
            organization_id=e.admin_unit_id,
            permissions=e.permissions,
        )
