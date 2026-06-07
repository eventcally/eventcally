"""Unit tests for schema_exporter and webhook_mapper_context."""

from unittest.mock import MagicMock, patch

from project.application.webhooks.abstract_url_provider import AbstractUrlProvider
from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.application.webhooks.schema_exporter import export_all_webhook_schemas
from project.application.webhooks.webhook_mapper_context import WebhookMapperContext
from project.infrastructure.services.flask_url_provider import FlaskUrlProvider


class TestSchemaExporter:
    def test_export_returns_non_empty_dict(self):
        result = export_all_webhook_schemas()
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_export_contains_expected_schema_keys(self):
        result = export_all_webhook_schemas()
        # Should contain at least one of these standard JSON Schema keys
        has_schema_keys = any(
            k in result for k in ("$defs", "title", "properties", "definitions")
        )
        assert has_schema_keys


class TestWebhookMapperContext:
    def test_instantiable(self):
        ctx = WebhookMapperContext(url_provider=MagicMock())
        assert ctx is not None
        assert isinstance(ctx, AbstractWebhookMapperContext)

    def test_get_image_url_delegates_to_url_provider(self):
        url_provider = MagicMock()
        url_provider.get_image_url.return_value = "http://img.example.com/1/12345"
        ctx = WebhookMapperContext(url_provider=url_provider)

        result = ctx.get_image_url(1, 12345)

        url_provider.get_image_url.assert_called_once_with(1, 12345)
        assert result == "http://img.example.com/1/12345"


class TestFlaskUrlProvider:
    def test_instantiable(self):
        provider = FlaskUrlProvider()
        assert provider is not None
        assert isinstance(provider, AbstractUrlProvider)

    def test_get_image_url_calls_url_for(self):
        with patch("flask.url_for") as mock_url_for:
            mock_url_for.return_value = "http://img.example.com/1/12345"
            provider = FlaskUrlProvider()

            result = provider.get_image_url(1, 12345)

            mock_url_for.assert_called_once_with("main.image", id=1, hash=12345)
            assert result == "http://img.example.com/1/12345"
