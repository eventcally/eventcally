from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppWebhookDeliveryListRequestSchema,
    AppWebhookDeliveryListResponseSchema,
)
from project.api.query_args import page_request_from_kwargs
from project.api.resources import BaseResource, require_api_access
from project.application.queries import ListWebhookDeliveriesForAppQuery
from project.views.utils import abort_if_page_out_of_range


class AppWebhookDeliveryListResource(BaseResource):
    @doc(summary="List webhook deliveries", tags=["Apps"])
    @use_kwargs(AppWebhookDeliveryListRequestSchema, location=("query"))
    @marshal_with(AppWebhookDeliveryListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, **kwargs):
        page = self.query_bus.handle(
            ListWebhookDeliveriesForAppQuery(
                app_id=current_token.app_id, page=page_request_from_kwargs(kwargs)
            )
        )
        abort_if_page_out_of_range(page)
        return page


add_api_resource(
    AppWebhookDeliveryListResource,
    "/app/webhook-deliveries",
    "api_v1_app_webhook_delivery_list",
)
