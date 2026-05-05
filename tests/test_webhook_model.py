from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from project.domain import events
from project.domain.commands.create_webhook import CreateWebhook
from project.domain.commands.update_webhook import UpdateWebhook
from project.domain.types import unset
from project.models.webhook import Webhook, before_saving_webhook


def test_create_returns_early_when_cmd_is_none():
    parent = SimpleNamespace(webhook=None)
    parent_event = SimpleNamespace(webhook=None)

    Webhook.create(None, parent, parent_event, field_name="webhook")

    assert parent.webhook is None
    assert parent_event.webhook is None


def test_create_sets_parent_and_parent_event_default_event_field_name():
    parent = SimpleNamespace(webhook=None)
    parent_event = SimpleNamespace(webhook=None)
    cmd = CreateWebhook(
        url="https://example.test/webhook",
        secret="secret",
        disabled=True,
        event_types=["event.created"],
    )

    Webhook.create(cmd, parent, parent_event, field_name="webhook")

    assert isinstance(parent.webhook, Webhook)
    assert parent.webhook.url == cmd.url
    assert parent.webhook.secret == cmd.secret
    assert parent.webhook.disabled is True
    assert parent.webhook.event_types == ["event.created"]

    assert isinstance(parent_event.webhook, events.WebhookCreated)
    assert parent_event.webhook.url == cmd.url
    assert parent_event.webhook.secret == cmd.secret
    assert parent_event.webhook.disabled is True
    assert parent_event.webhook.event_types == ["event.created"]


def test_create_uses_custom_event_field_name():
    parent = SimpleNamespace(webhook=None)
    parent_event = SimpleNamespace(custom_webhook_event=None)
    cmd = CreateWebhook(
        url="https://example.test/custom",
        secret=None,
        disabled=False,
        event_types=["event.updated"],
    )

    Webhook.create(
        cmd,
        parent,
        parent_event,
        field_name="webhook",
        event_field_name="custom_webhook_event",
    )

    assert isinstance(parent_event.custom_webhook_event, events.WebhookCreated)
    assert parent_event.custom_webhook_event.url == "https://example.test/custom"


def test_update_returns_early_when_cmd_is_unset():
    existing = Webhook()
    existing.url = "https://example.test/current"
    parent = SimpleNamespace(webhook=existing)
    parent_event = SimpleNamespace(webhook=None)

    Webhook.update(unset, parent, parent_event, field_name="webhook")

    assert parent.webhook is existing
    assert parent_event.webhook is None


def test_update_with_none_cmd_and_existing_instance_clears_parent_and_event():
    existing = Webhook()
    existing.url = "https://example.test/current"
    parent = SimpleNamespace(webhook=existing)
    parent_event = SimpleNamespace(webhook="sentinel")

    Webhook.update(None, parent, parent_event, field_name="webhook")

    assert parent.webhook is None
    assert parent_event.webhook is None


def test_update_with_none_cmd_and_missing_instance_returns_without_changes():
    parent = SimpleNamespace(webhook=None)
    parent_event = SimpleNamespace()

    Webhook.update(None, parent, parent_event, field_name="webhook")

    assert parent.webhook is None
    assert not hasattr(parent_event, "webhook")


def test_update_creates_instance_when_missing_and_sets_changed_event():
    parent = SimpleNamespace(webhook=None)
    parent_event = SimpleNamespace()
    cmd = UpdateWebhook(
        url="https://example.test/new",
        secret="new-secret",
        disabled=True,
        event_types=["event.created", "event.updated"],
    )

    Webhook.update(cmd, parent, parent_event, field_name="webhook")

    assert isinstance(parent.webhook, Webhook)
    assert parent.webhook.url == "https://example.test/new"
    assert parent.webhook.secret == "new-secret"
    assert parent.webhook.disabled is True
    assert parent.webhook.event_types == ["event.created", "event.updated"]

    assert isinstance(parent_event.webhook, events.WebhookUpdated)
    assert parent_event.webhook.url.old is None
    assert parent_event.webhook.url.new == "https://example.test/new"


def test_update_with_no_effective_changes_does_not_set_event():
    existing = Webhook()
    existing.url = "https://example.test/unchanged"
    existing.secret = "secret"
    existing.disabled = False
    existing.event_types = ["event.created"]

    parent = SimpleNamespace(webhook=existing)
    parent_event = SimpleNamespace()

    cmd = UpdateWebhook(
        url="https://example.test/unchanged",
        secret="secret",
        disabled=False,
        event_types=["event.created"],
    )

    Webhook.update(cmd, parent, parent_event, field_name="webhook")

    assert parent.webhook is existing
    assert not hasattr(parent_event, "webhook")


def test_update_uses_custom_event_field_name():
    existing = Webhook()
    existing.url = "https://example.test/old"
    parent = SimpleNamespace(webhook=existing)
    parent_event = SimpleNamespace(custom_event=None)

    cmd = UpdateWebhook(
        url="https://example.test/new",
        secret=unset,
        disabled=unset,
        event_types=unset,
    )

    Webhook.update(
        cmd,
        parent,
        parent_event,
        field_name="webhook",
        event_field_name="custom_event",
    )

    assert isinstance(parent_event.custom_event, events.WebhookUpdated)
    assert parent_event.custom_event.url.old == "https://example.test/old"
    assert parent_event.custom_event.url.new == "https://example.test/new"


def test_validate_raises_when_url_missing_and_passes_when_present():
    instance = Webhook()
    with pytest.raises(ValueError, match="URL is required for a webhook"):
        instance.validate()

    instance.url = "https://example.test/ok"
    instance.validate()


def test_is_empty_and_before_flush_branches():
    # Empty webhook with app clears logo.
    app = SimpleNamespace(logo="logo.png")
    empty_with_app = SimpleNamespace(
        app=app,
        is_empty=lambda: True,
    )
    Webhook.before_flush(empty_with_app, session=None, is_dirty=False)
    assert app.logo is None

    # Empty webhook without app does nothing.
    empty_no_app = SimpleNamespace(
        app=None,
        is_empty=lambda: True,
    )
    Webhook.before_flush(empty_no_app, session=None, is_dirty=False)
    assert empty_no_app.app is None

    # Non-empty webhook keeps app logo unchanged.
    non_empty = SimpleNamespace(
        app=SimpleNamespace(logo="keep.png"),
        is_empty=lambda: False,
    )
    Webhook.before_flush(non_empty, session=None, is_dirty=False)
    assert non_empty.app.logo == "keep.png"

    # Direct is_empty behavior.
    is_empty_target = SimpleNamespace(url=None)
    not_empty_target = SimpleNamespace(url="https://example.test/not-empty")
    assert Webhook.is_empty(is_empty_target) is True
    assert Webhook.is_empty(not_empty_target) is False


def test_before_saving_webhook_calls_validate():
    instance = SimpleNamespace(validate=Mock())

    before_saving_webhook(mapper=None, connect=None, self=instance)

    instance.validate.assert_called_once_with()
