from project.presentation.api.app.schemas.app_webhook_event_model_schema import (
    AppWebhookEventModelSchema,
)
from project.presentation.api.schemas import IdSchemaMixin


class AppWebhookEventIdSchema(AppWebhookEventModelSchema, IdSchemaMixin):
    pass
