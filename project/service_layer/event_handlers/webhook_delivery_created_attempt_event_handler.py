from project.domain import events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.service_layer.services.webhook_delivery_service import (
    WebhookDeliveryService,
)

from .abstract_event_handler import AbstractEventHandler


class WebhookDeliveryCreatedAttemptEventHandler(AbstractEventHandler):
    def __init__(self, webhook_delivery_service: WebhookDeliveryService):
        super().__init__()
        self.webhook_delivery_service = webhook_delivery_service

    def handle(self, event: events.WebhookDeliveryCreated, uow: AbstractUnitOfWork):
        with uow:
            self.webhook_delivery_service.send_webhook_delivery_sync(uow, event.id)
            uow.commit()
