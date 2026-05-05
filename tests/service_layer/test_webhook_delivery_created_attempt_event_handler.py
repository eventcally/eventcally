import datetime
from unittest.mock import Mock

from project.domain import events
from project.domain.types.actor import Actor
from project.service_layer.event_handlers.webhook_delivery_created_attempt_event_handler import (
    WebhookDeliveryCreatedAttemptEventHandler,
)


class _FakeUow:
    def __init__(self):
        self.commit = Mock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


def _make_uow():
    return _FakeUow()


def test_handle_calls_send_and_commits():
    service = Mock()
    handler = WebhookDeliveryCreatedAttemptEventHandler(
        webhook_delivery_service=service
    )
    event = events.WebhookDeliveryCreated(
        actor=Actor(),
        id=77,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )
    uow = _make_uow()

    handler.handle(event, uow)

    service.send_webhook_delivery_sync.assert_called_once_with(uow, 77)
    uow.commit.assert_called_once()
