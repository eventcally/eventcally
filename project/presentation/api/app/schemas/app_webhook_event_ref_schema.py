from marshmallow import fields, validate

from project.presentation.api.app.schemas.app_webhook_event_id_schema import (
    AppWebhookEventIdSchema,
)
from project.presentation.api.fields import GmtDateTimeField


class AppWebhookEventRefSchema(AppWebhookEventIdSchema):
    timestamp = GmtDateTimeField(dump_only=True)
    event_type = fields.String(required=True, validate=validate.Length(max=255))
