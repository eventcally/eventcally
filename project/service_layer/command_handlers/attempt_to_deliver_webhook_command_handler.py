from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.service_layer.services.webhook_delivery_service import (
    WebhookDeliveryService,
)

from .abstract_command_handler import AbstractCommandHandler


class AttemptToDeliverWebhookHandler(AbstractCommandHandler):
    def __init__(self, webhook_delivery_service: WebhookDeliveryService):
        super().__init__()
        self.webhook_delivery_service = webhook_delivery_service

    def handle(
        self, cmd: commands.AttemptToDeliverWebhookCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            self.webhook_delivery_service.send_webhook_delivery_sync(
                uow, cmd.webhook_delivery_id
            )
            uow.commit()
