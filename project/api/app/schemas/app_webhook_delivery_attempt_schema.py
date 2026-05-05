from project.api import marshmallow
from project.api.app.schemas.app_webhook_delivery_attempt_id_schema import (
    AppWebhookDeliveryAttemptIdSchema,
)
from project.api.fields import GmtDateTimeField


class AppWebhookDeliveryAttemptSchema(AppWebhookDeliveryAttemptIdSchema):
    url = marshmallow.auto_field(dump_only=True)
    status = marshmallow.auto_field(dump_only=True)
    status_code = marshmallow.auto_field(dump_only=True)
    start_at = GmtDateTimeField(dump_only=True)
    end_at = GmtDateTimeField(dump_only=True)
