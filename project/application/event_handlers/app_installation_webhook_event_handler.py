from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.app_installation_webhooks import (
    get_app_installation_webhook_info_by_event_type,
)
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
    events.EventOrganizerCreated: "event_organizer.created",
    events.EventOrganizerUpdated: "event_organizer.updated",
    events.EventOrganizerDeleted: "event_organizer.deleted",
    events.EventPlaceCreated: "event_place.created",
    events.EventPlaceUpdated: "event_place.updated",
    events.EventPlaceDeleted: "event_place.deleted",
}


class AppInstallationWebhookEventHandler(AbstractEventHandler):
    def __init__(self, mapper_context: AbstractWebhookMapperContext):
        super().__init__()
        self.mapper_context = mapper_context

    def handle(self, event: events.Event, uow: AbstractUnitOfWork):
        event_type = _EVENT_WEBHOOK_EVENT_TYPE.get(type(event))
        webhook_info = get_app_installation_webhook_info_by_event_type(event_type)
        required_permissions = webhook_info.permissions
        admin_unit_id = getattr(event, "admin_unit_id", None)

        with uow:
            installations = uow.organization_app_installations.get_all_with_webhook(
                admin_unit_id, required_permissions, webhook_info.event_type
            )

            if not installations:
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

            for installation in installations:
                webhook_delivery = WebhookDeliveryAggregate.create(
                    actor,
                    webhook_event_id=webhook_event.id,
                    app_id=installation.oauth2_client_id,
                    app_installation_id=installation.id,
                    webhook_id=installation.oauth2_client.webhook_id,
                )
                uow.webhook_deliveries.add(webhook_delivery)

            uow.commit()
