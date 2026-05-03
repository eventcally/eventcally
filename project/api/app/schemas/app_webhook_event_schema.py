from project.api import marshmallow
from project.api.app.schemas.app_webhook_event_id_schema import AppWebhookEventIdSchema
from project.api.fields import GmtDateTimeField


class AppWebhookEventSchema(AppWebhookEventIdSchema):
    timestamp = GmtDateTimeField(dump_only=True)
    event_type = marshmallow.auto_field()
