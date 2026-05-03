from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.types.actor import Actor
from project.models.webhook_delivery import WebhookDelivery
from project.models.webhook_event import WebhookEvent
from project.service_layer.webhooks.app_installation_webhooks import (
    get_app_installation_webhook_info_by_event_type,
)
from project.service_layer.webhooks.webhook_mapper_context import WebhookMapperContext

from .abstract_event_handler import AbstractEventHandler

_EVENT_WEBHOOK_EVENT_TYPE: dict[type, str] = {
    events.EventOrganizerCreated: "event_organizer.created",
    events.EventOrganizerUpdated: "event_organizer.updated",
    events.EventOrganizerDeleted: "event_organizer.deleted",
    events.EventPlaceCreated: "event_place.created",
    events.EventPlaceUpdated: "event_place.updated",
    events.EventPlaceDeleted: "event_place.deleted",
}


class AppInstallationWebhookEventHandler(AbstractEventHandler):
    def handle(self, event: events.Event, uow: AbstractUnitOfWork):
        event_type = _EVENT_WEBHOOK_EVENT_TYPE.get(type(event))
        webhook_info = get_app_installation_webhook_info_by_event_type(event_type)
        required_permissions = webhook_info.permissions
        admin_unit_id = getattr(event, "admin_unit_id", None)

        with uow:
            installations = uow.organizations.get_app_installations_with_webhook(
                admin_unit_id, required_permissions, webhook_info.event_type
            )

            if not installations:
                return

            mapper_context = WebhookMapperContext()
            payload_data = webhook_info.payload_cls.from_event(event, mapper_context)

            webhook_event = WebhookEvent(
                event_type=webhook_info.event_type,
                timestamp=event.timestamp,
                payload=payload_data.model_dump(),
            )

            webhook_deliverys = []

            for installation in installations:
                webhook_delivery = WebhookDelivery(
                    app_id=installation.oauth2_client_id,
                    app_installation_id=installation.id,
                    webhook_id=installation.oauth2_client.webhook_id,
                )
                webhook_event.deliveries.append(webhook_delivery)
                webhook_deliverys.append(webhook_delivery)

            uow.webhooks.add_event(webhook_event)
            uow.commit()

            for webhook_delivery in webhook_deliverys:
                uow.pending_events.append(
                    events.WebhookDeliveryCreated(actor=Actor(), id=webhook_delivery.id)
                )
