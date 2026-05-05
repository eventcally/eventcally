from project.api.app.schemas.app_webhook_delivery_model_schema import (
    AppWebhookDeliveryModelSchema,
)
from project.api.schemas import IdSchemaMixin


class AppWebhookDeliveryIdSchema(AppWebhookDeliveryModelSchema, IdSchemaMixin):
    pass
