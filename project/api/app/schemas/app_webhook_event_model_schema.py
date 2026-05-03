from project.api.schemas import SQLAlchemyBaseSchema
from project.models import WebhookEvent


class AppWebhookEventModelSchema(SQLAlchemyBaseSchema):
    class Meta:
        model = WebhookEvent
        load_instance = True
