"""Unit tests for webhook-related command handlers."""

from unittest.mock import MagicMock

from project.application import commands
from project.application.command_handlers.attempt_to_deliver_webhook_command_handler import (
    AttemptToDeliverWebhookHandler,
)
from project.application.command_handlers.delete_old_webhook_events_handler import (
    DeleteOldWebhookEventsHandler,
)
from project.domain.models.entities.actor import Actor

# ---------------------------------------------------------------------------
# DeleteOldWebhookEventsHandler
# ---------------------------------------------------------------------------


class TestDeleteOldWebhookEventsHandler:
    def test_calls_delete_old_events_with_3_days(self, uow):
        cmd = commands.DeleteOldWebhookEventsCommand.model_construct(actor=Actor())

        DeleteOldWebhookEventsHandler().handle(cmd, uow)

        assert uow.webhook_events.deleted_days == 3

    def test_commits(self, uow):
        cmd = commands.DeleteOldWebhookEventsCommand.model_construct(actor=Actor())

        DeleteOldWebhookEventsHandler().handle(cmd, uow)

        assert uow.committed

    def test_returns_deleted_count(self, uow):
        uow.webhook_events.delete_count = 5
        cmd = commands.DeleteOldWebhookEventsCommand.model_construct(actor=Actor())

        result = DeleteOldWebhookEventsHandler().handle(cmd, uow)

        assert result == 5


# ---------------------------------------------------------------------------
# AttemptToDeliverWebhookHandler
# ---------------------------------------------------------------------------


class TestAttemptToDeliverWebhookHandler:
    def test_calls_send_webhook_delivery_sync(self, uow):
        service = MagicMock()
        cmd = commands.AttemptToDeliverWebhookCommand.model_construct(
            actor=Actor(),
            webhook_delivery_id=42,
        )

        AttemptToDeliverWebhookHandler(webhook_delivery_service=service).handle(
            cmd, uow
        )

        service.send_webhook_delivery_sync.assert_called_once_with(uow, 42)

    def test_commits(self, uow):
        service = MagicMock()
        cmd = commands.AttemptToDeliverWebhookCommand.model_construct(
            actor=Actor(),
            webhook_delivery_id=1,
        )

        AttemptToDeliverWebhookHandler(webhook_delivery_service=service).handle(
            cmd, uow
        )

        assert uow.committed
