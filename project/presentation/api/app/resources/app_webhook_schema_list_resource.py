"""API resource for exporting webhook payload schemas."""

from flask_apispec import doc

from project.application.webhooks.schema_exporter import export_all_webhook_schemas
from project.presentation.api import add_api_resource
from project.presentation.api.resources import BaseResource


class AppWebhookSchemaListResource(BaseResource):
    """API resource for retrieving all webhook payload schemas."""

    @doc(
        summary="List webhook payload schemas",
        tags=["Apps"],
        description="Returns JSON Schema definitions for all available webhook payload models.",
    )
    def get(self):
        return export_all_webhook_schemas()


add_api_resource(
    AppWebhookSchemaListResource,
    "/app/webhooks/schemas",
    "api_v1_app_webhooks_schemas",
)
