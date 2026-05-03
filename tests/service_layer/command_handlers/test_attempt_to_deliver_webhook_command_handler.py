from unittest.mock import Mock

from project.domain import commands
from project.domain.types.actor import Actor
from project.service_layer.command_handlers.attempt_to_deliver_webhook_command_handler import (
    AttemptToDeliverWebhookHandler,
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
    handler = AttemptToDeliverWebhookHandler(webhook_delivery_service=service)
    cmd = commands.AttemptToDeliverWebhookCommand(actor=Actor(), webhook_delivery_id=55)
    uow = _make_uow()

    handler.handle(cmd, uow)

    service.send_webhook_delivery_sync.assert_called_once_with(uow, 55)
    uow.commit.assert_called_once()
