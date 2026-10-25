import pytest


def test_value_object_roundtrip_and_event_type_check(app):
    from project.domain.models.value_objects.webhook_value_object import (
        WebhookValueObject,
    )
    from project.infrastructure.models import Webhook

    webhook = Webhook()
    webhook.fill_from_value_object(
        WebhookValueObject(
            url="https://example.com/hook",
            secret="secret",
            disabled=False,
            event_types=["event.created"],
        )
    )

    value = webhook.to_value_object()

    assert value.url == "https://example.com/hook"
    assert value.secret == "secret"
    assert webhook.is_enabled_for_event_type("event.created")
    assert not webhook.is_enabled_for_event_type("event.updated")
    webhook.disabled = True
    assert not webhook.is_enabled_for_event_type("event.created")


def test_validate_requires_url(app):
    from project.infrastructure.models import Webhook

    with pytest.raises(ValueError, match="URL is required"):
        Webhook(url="").validate()

    Webhook(url="https://example.com/hook").validate()


def test_before_flush_of_empty_webhook_keeps_it_on_its_app(app):
    from project.infrastructure.models import OAuth2Client, Webhook

    webhook = Webhook(url="")
    client = OAuth2Client()
    client.webhook = webhook

    assert webhook.is_empty()
    webhook.before_flush(None, is_dirty=True)

    assert client.webhook is webhook


def test_before_flush_of_webhook_without_app_does_nothing(app):
    from project.infrastructure.models import Webhook

    Webhook(url="").before_flush(None, is_dirty=True)
