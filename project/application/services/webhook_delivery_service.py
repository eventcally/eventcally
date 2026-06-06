import datetime
import logging

from project.application.read_repositories.abstract_webhook_delivery_read_repository import (
    AbstractWebhookDeliveryReadRepository,
)
from project.application.services.abstract_webhook_delivery_sender import (
    AbstractWebhookDeliverySender,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.domain.models.entities.actor import Actor


class WebhookDeliveryService:
    def __init__(
        self,
        logger: logging.Logger,
        webhook_delivery_sender: AbstractWebhookDeliverySender,
        webhook_delivery_read_repo: AbstractWebhookDeliveryReadRepository,
    ):
        self.logger = logger
        self.webhook_delivery_sender = webhook_delivery_sender
        self.webhook_delivery_read_repo = webhook_delivery_read_repo

    def send_webhook_delivery_sync(
        self, uow: AbstractUnitOfWork, webhook_delivery_id: int
    ):
        webhook_delivery = self.webhook_delivery_read_repo.get(webhook_delivery_id)
        if not webhook_delivery:
            return

        webhook_event = webhook_delivery.webhook_event
        webhook = webhook_delivery.webhook
        webhook_delivery_id = webhook_delivery.id
        url = webhook.url
        secret = webhook.secret
        json_dict = webhook_event.payload
        event_type = webhook_event.event_type
        app_installation_id = webhook_delivery.app_installation_id

        start_at = datetime.datetime.now(datetime.timezone.utc)

        status, status_code = self.webhook_delivery_sender.send(
            url=url,
            secret=secret,
            payload=json_dict,
            event_type=event_type,
            webhook_delivery_id=webhook_delivery_id,
            app_installation_id=app_installation_id,
        )
        end_at = datetime.datetime.now(datetime.timezone.utc)

        attempt = WebhookDeliveryAttemptAggregate.create(
            actor=Actor(),
            url=url,
            status=status,
            webhook_delivery_id=webhook_delivery_id,
            status_code=status_code,
            start_at=start_at,
            end_at=end_at,
        )
        uow.webhook_delivery_attempts.add(attempt)
