import abc

from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)


class AbstractWebhookDeliveryRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add(self, event: WebhookDeliveryAggregate):
        self._add(event)
        self.seen.add(event)

    def get(self, object_id: int) -> WebhookDeliveryAggregate:
        delivery = self._get(object_id)
        if delivery:
            self.seen.add(delivery)
        return delivery

    @abc.abstractmethod
    def _add(self, event: WebhookDeliveryAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> WebhookDeliveryAggregate:  # pragma: no cover
        raise NotImplementedError
