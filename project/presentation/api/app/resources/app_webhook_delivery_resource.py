from authlib.integrations.flask_oauth2 import current_token
from flask_apispec import doc, marshal_with

from project.application.queries import GetWebhookDeliveryForAppQuery
from project.presentation.api import add_api_resource
from project.presentation.api.app.schemas import AppWebhookDeliverySchema
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.shared.query_results import result_or_404


class AppWebhookDeliveryResource(BaseResource):
    @doc(
        summary="Get webhook delivery",
        tags=["Apps"],
    )
    @marshal_with(AppWebhookDeliverySchema)
    @require_api_access(app_token_required=True)
    def get(self, id):
        return result_or_404(
            self.query_bus.handle(
                GetWebhookDeliveryForAppQuery(app_id=current_token.app_id, id=id)
            )
        )


add_api_resource(
    AppWebhookDeliveryResource,
    "/app/webhook-deliveries/<int:id>",
    "api_v1_app_webhook_delivery",
)
