import abc

from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)


class AbstractWebhookDeliveryAttemptRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add(self, event: WebhookDeliveryAttemptAggregate):
        self._add(event)
        self.seen.add(event)

    def get(self, object_id: int) -> WebhookDeliveryAttemptAggregate:
        attempt = self._get(object_id)
        if attempt:
            self.seen.add(attempt)
        return attempt

    @abc.abstractmethod
    def _add(self, event: WebhookDeliveryAttemptAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> WebhookDeliveryAttemptAggregate:  # pragma: no cover
        raise NotImplementedError
