"""Unit tests for WebhookDeliveryService orchestration."""

import logging
from unittest.mock import MagicMock

from project.application.services.webhook_delivery_service import WebhookDeliveryService


class _FakeWebhook:
    def __init__(self, url="http://example.com/hook", secret=None):
        self.url = url
        self.secret = secret


class _FakeWebhookEvent:
    def __init__(self, payload=None, event_type="test.event"):
        self.payload = payload or {"key": "value"}
        self.event_type = event_type


class _FakeWebhookDelivery:
    def __init__(
        self,
        delivery_id=123,
        app_installation_id=456,
        webhook=None,
        webhook_event=None,
    ):
        self.id = delivery_id
        self.app_installation_id = app_installation_id
        self.webhook = webhook or _FakeWebhook()
        self.webhook_event = webhook_event or _FakeWebhookEvent()


def _make_service(status="OK", status_code=None):
    sender = MagicMock()
    sender.send.return_value = (status, status_code)
    webhook_delivery_read_repo = MagicMock()
    webhook_delivery_read_repo.get.return_value = None
    service = WebhookDeliveryService(
        logger=logging.getLogger("test"),
        webhook_delivery_sender=sender,
        webhook_delivery_read_repo=webhook_delivery_read_repo,
    )
    return service, sender, webhook_delivery_read_repo


class TestWebhookDeliveryService:
    def test_delivery_not_found_returns_early(self, uow):
        service, sender, webhook_delivery_read_repo = _make_service()

        service.send_webhook_delivery_sync(uow, 9999)

        webhook_delivery_read_repo.get.assert_called_once_with(9999)
        sender.send.assert_not_called()
        assert len(uow.webhook_delivery_attempts._store) == 0

    def test_delivery_is_sent_and_attempt_is_recorded(self, uow):
        service, sender, webhook_delivery_read_repo = _make_service(
            status="DELIVERED", status_code="202"
        )
        delivery = _FakeWebhookDelivery(
            delivery_id=77,
            app_installation_id=88,
            webhook=_FakeWebhook(
                url="https://example.com/webhook",
                secret="super-secret",
            ),
            webhook_event=_FakeWebhookEvent(
                payload={"event": "payload"},
                event_type="app.installation.updated",
            ),
        )
        webhook_delivery_read_repo.get.return_value = delivery

        service.send_webhook_delivery_sync(uow, 77)

        sender.send.assert_called_once_with(
            url="https://example.com/webhook",
            secret="super-secret",
            payload={"event": "payload"},
            event_type="app.installation.updated",
            webhook_delivery_id=77,
            app_installation_id=88,
        )

        assert len(uow.webhook_delivery_attempts._store) == 1
        attempt = next(iter(uow.webhook_delivery_attempts._store.values()))
        assert attempt.url == "https://example.com/webhook"
        assert attempt.webhook_delivery_id == 77
        assert attempt.status == "DELIVERED"
        assert attempt.status_code == "202"
        assert attempt.start_at.tzinfo is not None
        assert attempt.end_at.tzinfo is not None
        assert attempt.end_at >= attempt.start_at
