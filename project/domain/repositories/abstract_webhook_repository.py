import abc

from project.models.webhook_delivery import WebhookDelivery
from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt
from project.models.webhook_event import WebhookEvent


class AbstractWebhookRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add_event(self, event: WebhookEvent):
        self._add_event(event)
        self.seen.add(event)

    def get_delivery(self, object_id: int) -> WebhookDelivery:
        delivery = self._get_delivery(object_id)
        if delivery:
            self.seen.add(delivery)
        return delivery

    def get_delivery_attempt(self, object_id: int) -> WebhookDeliveryAttempt:
        delivery_attempt = self._get_delivery_attempt(object_id)
        if delivery_attempt:
            self.seen.add(delivery_attempt)
        return delivery_attempt

    def delete_old_events(self, days: int) -> int:
        return self._delete_old_events(days)

    @abc.abstractmethod
    def _add_event(self, event: WebhookEvent):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_delivery(self, object_id: int) -> WebhookDelivery:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_delivery_attempt(
        self, object_id: int
    ) -> WebhookDeliveryAttempt:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _delete_old_events(self, days: int) -> int:  # pragma: no cover
        raise NotImplementedError
