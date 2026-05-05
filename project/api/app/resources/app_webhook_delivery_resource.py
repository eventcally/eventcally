from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with

from project.api import add_api_resource
from project.api.app.schemas import AppWebhookDeliverySchema
from project.api.resources import BaseResource, require_api_access
from project.models import WebhookDelivery


class AppWebhookDeliveryResource(BaseResource):
    @doc(
        summary="Get webhook delivery",
        tags=["Apps"],
    )
    @marshal_with(AppWebhookDeliverySchema)
    @require_api_access(app_token_required=True)
    def get(self, id):
        return (
            WebhookDelivery.query.filter(WebhookDelivery.app_id == current_token.app_id)
            .filter(WebhookDelivery.id == id)
            .first_or_404()
        )


add_api_resource(
    AppWebhookDeliveryResource,
    "/app/webhook-deliveries/<int:id>",
    "api_v1_app_webhook_delivery",
)
