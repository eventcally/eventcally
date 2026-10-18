from marshmallow import fields

from project.presentation.api.app.schemas.app_webhook_delivery_ref_schema import (
    AppWebhookDeliveryRefSchema,
)
from project.presentation.api.schemas import PaginationResponseSchema


class AppWebhookDeliveryListResponseSchema(PaginationResponseSchema):
    items = fields.List(
        fields.Nested(AppWebhookDeliveryRefSchema),
        metadata={"description": "Webhook deliveries"},
    )
