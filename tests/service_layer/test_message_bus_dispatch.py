"""Tests for MessageBus.dispatch_command – lines 61-63."""

from types import SimpleNamespace
from unittest.mock import Mock

from project.domain import commands
from project.domain.types.actor import Actor
from project.service_layer.message_bus import MessageBus


def _make_message_bus():
    context_provider = SimpleNamespace(current_actor=Actor())
    command_dispatcher = Mock()
    return (
        MessageBus(
            uow_factory=Mock(),
            context_provider=context_provider,
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
