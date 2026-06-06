import abc

from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)


class AbstractWebhookEventRepository(abc.ABC):
    def __init__(self):
        self.seen = set()

    def add(self, event: WebhookEventAggregate):
        self._add(event)
        self.seen.add(event)

    def get(self, object_id: int) -> WebhookEventAggregate:
        event = self._get(object_id)
        if event:
            self.seen.add(event)
        return event

    def delete_old_events(self, days: int) -> int:
        return self._delete_old_events(days)

    @abc.abstractmethod
    def _add(self, event: WebhookEventAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> WebhookEventAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _delete_old_events(self, days: int) -> int:  # pragma: no cover
        raise NotImplementedError
