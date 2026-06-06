"""Tests for micro-gap coverage in various model, domain, i10n, container, init modules."""

import pytest

from project.application.commands.update_app_command import UpdateAppCommand
from project.models.webhook import Webhook

# ---------------------------------------------------------------------------
# update_app_command.py line 25 – validator raises ValueError for empty list
# ---------------------------------------------------------------------------


def test_update_app_command_raises_for_empty_permissions():
    with pytest.raises(ValueError, match="at least one"):
        UpdateAppCommand.model_validate({"actor": {}, "id": 1, "app_permissions": []})


def test_update_app_command_accepts_none_permissions():
    cmd = UpdateAppCommand.model_validate({"actor": {}, "id": 1})
    # app_permissions is unset, which is distinct from empty list
    assert cmd.id == 1


# ---------------------------------------------------------------------------
# webhook.py line 86 – is_enabled_for_event_type
# ---------------------------------------------------------------------------


def test_webhook_is_enabled_for_event_type_true():
    webhook = Webhook()
    webhook.url = "https://example.test/hook"
    webhook.disabled = False
    webhook.event_types = ["app_installation.created", "app_installation.deleted"]

    assert webhook.is_enabled_for_event_type("app_installation.created") is True


def test_webhook_is_enabled_for_event_type_false_when_disabled():
    webhook = Webhook()
    webhook.url = "https://example.test/hook"
    webhook.disabled = True
    webhook.event_types = ["app_installation.created"]

    assert not webhook.is_enabled_for_event_type("app_installation.created")


def test_webhook_is_enabled_for_event_type_false_when_not_in_list():
    webhook = Webhook()
    webhook.url = "https://example.test/hook"
    webhook.disabled = False
    webhook.event_types = ["app_installation.deleted"]

    assert not webhook.is_enabled_for_event_type("app_installation.created")
