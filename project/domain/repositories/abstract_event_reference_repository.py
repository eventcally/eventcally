import abc
from typing import Optional, Set

from project.domain.models.aggregates.event_reference_aggregate import (
    EventReferenceAggregate,
)


class AbstractEventReferenceRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventReferenceAggregate] = set()

    def get_by_event_id(self, event_id: int) -> list[EventReferenceAggregate]:
        event_references = self._get_by_event_id(event_id)
        self.seen.update(event_references)
        return event_references

    def add(self, event_reference: EventReferenceAggregate):
        self._add(event_reference)
        self.seen.add(event_reference)

    def update(self, event_reference: EventReferenceAggregate):
        self._update(event_reference)
        self.seen.add(event_reference)

    def get(self, object_id: int) -> Optional[EventReferenceAggregate]:
        event_reference = self._get(object_id)
        if event_reference:
            self.seen.add(event_reference)
        return event_reference

    def remove(self, event_reference: EventReferenceAggregate):
        self._remove(event_reference)
        self.seen.add(event_reference)

    @abc.abstractmethod
    def _get_by_event_id(
        self, event_id: int
    ) -> list[EventReferenceAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _add(self, event_reference: EventReferenceAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, event_reference: EventReferenceAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[EventReferenceAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event_reference: EventReferenceAggregate):  # pragma: no cover
        raise NotImplementedError
