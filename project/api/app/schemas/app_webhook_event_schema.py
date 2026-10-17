from marshmallow import fields, validate

from project.api.app.schemas.app_webhook_event_id_schema import AppWebhookEventIdSchema
from project.api.fields import GmtDateTimeField


class AppWebhookEventSchema(AppWebhookEventIdSchema):
    timestamp = GmtDateTimeField(dump_only=True)
    event_type = fields.String(required=True, validate=validate.Length(max=255))
