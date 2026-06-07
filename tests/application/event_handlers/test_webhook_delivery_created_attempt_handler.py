"""Unit tests for WebhookDeliveryCreatedAttemptEventHandler."""

from unittest.mock import MagicMock

from project.application.event_handlers.webhook_delivery_created_attempt_event_handler import (
    WebhookDeliveryCreatedAttemptEventHandler,
)
from project.domain import events
from project.domain.models.entities.actor import Actor


class TestWebhookDeliveryCreatedAttemptEventHandler:
    def test_calls_send_webhook_delivery_sync_with_event_id(self, uow):
        service = MagicMock()
        actor = Actor()
        ev = events.WebhookDeliveryCreated(actor=actor, id=77)
        handler = WebhookDeliveryCreatedAttemptEventHandler(
            webhook_delivery_service=service
        )

        handler.handle(ev, uow)

        service.send_webhook_delivery_sync.assert_called_once_with(uow, 77)

    def test_commits(self, uow):
        service = MagicMock()
        actor = Actor()
        ev = events.WebhookDeliveryCreated(actor=actor, id=1)
        handler = WebhookDeliveryCreatedAttemptEventHandler(
            webhook_delivery_service=service
        )

        handler.handle(ev, uow)

        assert uow.committed
