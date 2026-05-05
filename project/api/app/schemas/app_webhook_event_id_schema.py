from project.api.app.schemas.app_webhook_event_model_schema import (
    AppWebhookEventModelSchema,
)
from project.api.schemas import IdSchemaMixin


class AppWebhookEventIdSchema(AppWebhookEventModelSchema, IdSchemaMixin):
    pass
