"""Tests for MessageBus.dispatch_command – lines 61-63."""

from types import SimpleNamespace
from unittest.mock import Mock

from project.application import commands
from project.application.message_bus import MessageBus
from project.domain.models.entities.actor import Actor


def _make_message_bus():
    app_context_provider = SimpleNamespace(get_current_actor=lambda: Actor())
    command_dispatcher = Mock()
    return (
        MessageBus(
            uow_factory=Mock(),
            app_context_provider=app_context_provider,
            command_handler_factory=Mock(),
            event_handler_factory=Mock(),
            event_dispatcher=Mock(),
            command_dispatcher=command_dispatcher,
        ),
        command_dispatcher,
    )


def test_dispatch_command_calls_dispatcher():
    bus, command_dispatcher = _make_message_bus()
    cmd = commands.AttemptToDeliverWebhookCommand.model_construct(
        webhook_delivery_id=42
    )

    bus.dispatch_command(cmd)

    command_dispatcher.dispatch.assert_called_once_with(cmd)
