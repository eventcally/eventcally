from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from project.models.webhook import Webhook, before_saving_webhook


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
