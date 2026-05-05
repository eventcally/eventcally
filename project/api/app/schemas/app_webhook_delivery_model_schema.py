from project.api.schemas import SQLAlchemyBaseSchema
from project.models import WebhookDelivery


class AppWebhookDeliveryModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = WebhookDelivery
        load_instance = True
