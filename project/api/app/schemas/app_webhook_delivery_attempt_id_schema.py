from project.api.app.schemas.app_webhook_delivery_attempt_model_schema import (
    AppWebhookDeliveryAttemptModelSchema,
)
from project.api.schemas import IdSchemaMixin


class AppWebhookDeliveryAttemptIdSchema(
    AppWebhookDeliveryAttemptModelSchema, IdSchemaMixin
):
    pass
