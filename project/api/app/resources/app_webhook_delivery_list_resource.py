from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppWebhookDeliveryListRequestSchema,
    AppWebhookDeliveryListResponseSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.models import WebhookDelivery
from project.models.webhook_event import WebhookEvent


class AppWebhookDeliveryListResource(BaseResource):
    @doc(summary="List webhook deliveries", tags=["Apps"])
    @use_kwargs(AppWebhookDeliveryListRequestSchema, location=("query"))
    @marshal_with(AppWebhookDeliveryListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, **kwargs):
        query = WebhookDelivery.query.filter(
            WebhookDelivery.app_id == current_token.app_id
        )
        query = query.join(WebhookDelivery.webhook_event).order_by(
            WebhookEvent.timestamp.desc()
        )

        return query.paginate()


add_api_resource(
    AppWebhookDeliveryListResource,
    "/app/webhook-deliveries",
    "api_v1_app_webhook_delivery_list",
)
