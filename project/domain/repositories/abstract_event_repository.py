import abc
from typing import Set

from project.domain.models.aggregates.event_aggregate import EventAggregate


class AbstractEventRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventAggregate] = set()

    def add(self, event: EventAggregate):
        self._add(event)
        self.seen.add(event)

    def update(self, event: EventAggregate):
        self._update(event)
        self.seen.add(event)

    def get(self, object_id: int) -> EventAggregate:
        event = self._get(object_id)
        if event:
            self.seen.add(event)
        return event

    def remove(self, event: EventAggregate):
        self._remove(event)
        self.seen.add(event)

    @abc.abstractmethod
    def _add(self, event: EventAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, event: EventAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> EventAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event: EventAggregate):  # pragma: no cover
        raise NotImplementedError
