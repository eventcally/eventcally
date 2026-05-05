from authlib.integrations.flask_oauth2 import current_token
from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project.api import add_api_resource
from project.api.app.schemas import (
    AppWebhookDeliveryAttemptListRequestSchema,
    AppWebhookDeliveryAttemptListResponseSchema,
    AppWebhookDeliveryAttemptTriggerRequestSchema,
)
from project.api.resources import BaseResource, require_api_access
from project.domain.commands import AttemptToDeliverWebhookCommand
from project.models import WebhookDelivery, WebhookDeliveryAttempt


class AppWebhookDeliveryAttemptListResource(BaseResource):
    @doc(summary="List webhook delivery attempts", tags=["Apps"])
    @use_kwargs(AppWebhookDeliveryAttemptListRequestSchema, location=("query"))
    @marshal_with(AppWebhookDeliveryAttemptListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, id, **kwargs):
        # First verify the webhook delivery belongs to the current app
        delivery = (
            WebhookDelivery.query.filter(WebhookDelivery.app_id == current_token.app_id)
            .filter(WebhookDelivery.id == id)
            .first_or_404()
        )

        query = WebhookDeliveryAttempt.query.filter(
            WebhookDeliveryAttempt.webhook_delivery_id == delivery.id
        )
        query = query.order_by(WebhookDeliveryAttempt.start_at.desc())

        return query.paginate()

    @doc(summary="Trigger new webhook delivery attempt", tags=["Apps"])
    @use_kwargs(
        AppWebhookDeliveryAttemptTriggerRequestSchema, location="json", apply=False
    )
    @marshal_with(None, 204)
    @require_api_access(app_token_required=True)
    def post(self, id):
        # First verify the webhook delivery belongs to the current app
        delivery = (
            WebhookDelivery.query.filter(WebhookDelivery.app_id == current_token.app_id)
            .filter(WebhookDelivery.id == id)
            .first_or_404()
        )

        cmd = AttemptToDeliverWebhookCommand.model_construct(
            webhook_delivery_id=delivery.id
        )
        self.message_bus.dispatch_command(cmd)

        return make_response("", 204)


add_api_resource(
    AppWebhookDeliveryAttemptListResource,
    "/app/webhook-deliveries/<int:id>/attempts",
    "api_v1_app_webhook_delivery_attempt_list",
)
