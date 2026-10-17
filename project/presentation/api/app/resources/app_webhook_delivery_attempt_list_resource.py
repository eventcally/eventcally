from authlib.integrations.flask_oauth2 import current_token
from flask import make_response
from flask_apispec import doc, marshal_with, use_kwargs

from project.application.commands import AttemptToDeliverWebhookCommand
from project.application.queries import (
    GetWebhookDeliveryForAppQuery,
    ListWebhookDeliveryAttemptsForAppQuery,
)
from project.presentation.api import add_api_resource
from project.presentation.api.app.schemas import (
    AppWebhookDeliveryAttemptListRequestSchema,
    AppWebhookDeliveryAttemptListResponseSchema,
    AppWebhookDeliveryAttemptTriggerRequestSchema,
)
from project.presentation.api.resources import BaseResource, require_api_access
from project.presentation.shared.query_args import page_request_from_kwargs
from project.presentation.shared.query_results import (
    abort_if_page_out_of_range,
    result_or_404,
)


class AppWebhookDeliveryAttemptListResource(BaseResource):
    @doc(summary="List webhook delivery attempts", tags=["Apps"])
    @use_kwargs(AppWebhookDeliveryAttemptListRequestSchema, location=("query"))
    @marshal_with(AppWebhookDeliveryAttemptListResponseSchema)
    @require_api_access(app_token_required=True)
    def get(self, id, **kwargs):
        page = result_or_404(
            self.query_bus.handle(
                ListWebhookDeliveryAttemptsForAppQuery(
                    app_id=current_token.app_id,
                    webhook_delivery_id=id,
                    page=page_request_from_kwargs(kwargs),
                )
            )
        )
        abort_if_page_out_of_range(page)
        return page

    @doc(summary="Trigger new webhook delivery attempt", tags=["Apps"])
    @use_kwargs(
        AppWebhookDeliveryAttemptTriggerRequestSchema, location="json", apply=False
    )
    @marshal_with(None, 204)
    @require_api_access(app_token_required=True)
    def post(self, id):
        # First verify the webhook delivery belongs to the current app
        delivery = result_or_404(
            self.query_bus.handle(
                GetWebhookDeliveryForAppQuery(app_id=current_token.app_id, id=id)
            )
        )

        cmd = AttemptToDeliverWebhookCommand(
            webhook_delivery_id=delivery.id,
            actor=self.app_context_provider.get_current_actor(),
        )
        self.message_bus.dispatch_command(cmd)

        return make_response("", 204)


add_api_resource(
    AppWebhookDeliveryAttemptListResource,
    "/app/webhook-deliveries/<int:id>/attempts",
    "api_v1_app_webhook_delivery_attempt_list",
)
