from marshmallow import fields, validate

from project.presentation.api.app.schemas.app_webhook_delivery_attempt_id_schema import (
    AppWebhookDeliveryAttemptIdSchema,
)
from project.presentation.api.fields import GmtDateTimeField


class AppWebhookDeliveryAttemptSchema(AppWebhookDeliveryAttemptIdSchema):
    url = fields.String(
        required=True, dump_only=True, validate=validate.Length(max=255)
    )
    status = fields.String(
        allow_none=True, dump_only=True, validate=validate.Length(max=255)
    )
    status_code = fields.String(
        allow_none=True, dump_only=True, validate=validate.Length(max=255)
    )
    start_at = GmtDateTimeField(dump_only=True)
    end_at = GmtDateTimeField(dump_only=True)
