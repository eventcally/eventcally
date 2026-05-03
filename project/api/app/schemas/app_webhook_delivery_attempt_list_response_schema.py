from marshmallow import fields

from project.api.app.schemas.app_webhook_delivery_attempt_ref_schema import (
    AppWebhookDeliveryAttemptRefSchema,
)
from project.api.schemas import PaginationResponseSchema


class AppWebhookDeliveryAttemptListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppWebhookDeliveryAttemptRefSchema),
        metadata={"description": "Webhook delivery attempts"},
    )
