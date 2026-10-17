from marshmallow import fields

from project.presentation.api.app.schemas.app_installation_ref_schema import (
    AppInstallationRefSchema,
)
from project.presentation.api.app.schemas.app_webhook_delivery_id_schema import (
    AppWebhookDeliveryIdSchema,
)
from project.presentation.api.app.schemas.app_webhook_event_schema import (
    AppWebhookEventSchema,
)


class AppWebhookDeliverySchema(AppWebhookDeliveryIdSchema):
    webhook_event = fields.Nested(AppWebhookEventSchema)
    app_installation = fields.Nested(AppInstallationRefSchema)
