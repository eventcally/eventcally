from project.api.schemas import SQLAlchemyBaseSchema
from project.models import WebhookDeliveryAttempt


class AppWebhookDeliveryAttemptModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = WebhookDeliveryAttempt
        load_instance = True
