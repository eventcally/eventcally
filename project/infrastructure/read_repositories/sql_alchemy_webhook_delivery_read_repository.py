from typing import Optional

from project.application.read_models.webhook_delivery_read_model import (
    WebhookDeliveryReadModel,
)
from project.application.read_repositories.abstract_webhook_delivery_read_repository import (
    AbstractWebhookDeliveryReadRepository,
)
from project.models.webhook_delivery import WebhookDelivery


class SqlAlchemyWebhookDeliveryReadRepository(AbstractWebhookDeliveryReadRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _get_model(self, object_id: int) -> Optional[WebhookDelivery]:
        return self.session.query(WebhookDelivery).filter_by(id=object_id).first()

    def get(self, object_id: int) -> Optional[WebhookDeliveryReadModel]:
        model = self._get_model(object_id)
        return WebhookDelivery.to_read_model(model)
