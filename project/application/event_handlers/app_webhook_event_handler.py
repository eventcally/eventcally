from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.app_webhooks import get_app_webhook_info_by_event_type
from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.domain.models.entities.actor import Actor

from .abstract_event_handler import AbstractEventHandler

_EVENT_WEBHOOK_EVENT_TYPE: dict[type, str] = {
    events.AppInstallationCreated: "app_installation.created",
    events.AppInstallationPermissionsUpdated: "app_installation.permissions_updated",
    events.AppInstallationDeleted: "app_installation.deleted",
}


class AppWebhookEventHandler(AbstractEventHandler):
    def __init__(self, mapper_context: AbstractWebhookMapperContext):
        super().__init__()
        self.mapper_context = mapper_context

    def handle(self, event: events.Event, uow: AbstractUnitOfWork):
        event_type = _EVENT_WEBHOOK_EVENT_TYPE.get(type(event))
        webhook_info = get_app_webhook_info_by_event_type(event_type)
        app_id = getattr(event, "app_id", None)

        with uow:
            app = uow.apps.get(app_id)

            if (
                not app
                or not app.webhook
                or not app.webhook.is_enabled_for_event_type(event_type)
            ):
                return

            payload_data = webhook_info.payload_cls.from_event(
                event, self.mapper_context
            )
            actor = Actor()

            webhook_event = WebhookEventAggregate.create(
                actor,
                event_type=webhook_info.event_type,
                timestamp=event.timestamp,
                payload=payload_data.model_dump(),
            )
            uow.webhook_events.add(webhook_event)

            webhook_delivery = WebhookDeliveryAggregate.create(
                actor,
                webhook_event_id=webhook_event.id,
                app_id=app.id,
                webhook_id=app.webhook.id,
            )
            uow.webhook_deliveries.add(webhook_delivery)

            uow.commit()
