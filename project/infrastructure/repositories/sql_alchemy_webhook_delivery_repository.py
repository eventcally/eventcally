from typing import Optional

from project.domain.events.webhook_delivery_created import WebhookDeliveryCreated
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.domain.repositories.abstract_webhook_delivery_repository import (
    AbstractWebhookDeliveryRepository,
)
from project.models.webhook_delivery import WebhookDelivery


class SqlAlchemyWebhookDeliveryRepository(AbstractWebhookDeliveryRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, delivery: WebhookDeliveryAggregate):
        model = WebhookDelivery.from_aggregate(delivery)
        self.session.add(model)
        self.session.flush()

        domain_event = delivery.get_first_domain_event_by_type(WebhookDeliveryCreated)
        delivery.id = model.id
        domain_event.id = model.id

    def _get_model(self, object_id: int) -> Optional[WebhookDelivery]:
        return self.session.query(WebhookDelivery).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[WebhookDeliveryAggregate]:
        model = self._get_model(object_id)
        return WebhookDelivery.to_aggregate(model)
