from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.types.actor import Actor
from project.models.webhook_delivery import WebhookDelivery
from project.models.webhook_event import WebhookEvent
from project.service_layer.webhooks.app_webhooks import (
    get_app_webhook_info_by_event_type,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext

from .abstract_event_handler import AbstractEventHandler

_EVENT_WEBHOOK_EVENT_TYPE: dict[type, str] = {
    events.AppInstallationCreated: "app.installed",
    events.AppInstallationPermissionsUpdated: "app_installation.permissions_updated",
    events.AppUninstalled: "app.uninstalled",
}


class AppWebhookEventHandler(AbstractEventHandler):
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

            mapper_context = WebhookMapperContext()
            payload_data = webhook_info.payload_cls.from_event(event, mapper_context)

            webhook_event = WebhookEvent(
                event_type=webhook_info.event_type,
                timestamp=event.timestamp,
                payload=payload_data.model_dump(),
            )

            webhook_delivery = WebhookDelivery(
                app_id=app.id,
                webhook_id=app.webhook.id,
            )
            webhook_event.deliveries.append(webhook_delivery)

            uow.webhooks.add_event(webhook_event)
            uow.commit()
            uow.pending_events.append(
                events.WebhookDeliveryCreated(actor=Actor(), id=webhook_delivery.id)
            )
