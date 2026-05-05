import sys
from unittest.mock import MagicMock

from project.domain import commands
from project.domain.types.actor import Actor
from project.infrastructure.celery_command_dispatcher import CeleryCommandDispatcher


def test_dispatch_calls_process_delayed_command(monkeypatch):
    dispatcher = CeleryCommandDispatcher()
    cmd = commands.AttemptToDeliverWebhookCommand(
        actor=Actor(), webhook_delivery_id=123
    )

    fake_task = MagicMock()

    # The dispatch method does `from project.base_tasks import process_delayed_command`
    # at call time, so we inject a fake module into sys.modules before the call.
    fake_base_tasks = MagicMock()
    fake_base_tasks.process_delayed_command = fake_task
    monkeypatch.setitem(sys.modules, "project.base_tasks", fake_base_tasks)

    dispatcher.dispatch(cmd)

    expected_class_path = f"{cmd.__class__.__module__}.{cmd.__class__.__name__}"
    expected_dict = cmd.model_dump(exclude_unset=True)
    fake_task.delay.assert_called_once_with(expected_class_path, expected_dict)
