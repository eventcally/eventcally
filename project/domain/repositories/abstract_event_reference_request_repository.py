import abc
from typing import Optional, Set

from project.domain.models.aggregates.event_reference_request_aggregate import (
    EventReferenceRequestAggregate,
)


class AbstractEventReferenceRequestRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventReferenceRequestAggregate] = set()

    def add(self, event_reference_request: EventReferenceRequestAggregate):
        self._add(event_reference_request)
        self.seen.add(event_reference_request)

    def update(self, event_reference_request: EventReferenceRequestAggregate):
        self._update(event_reference_request)
        self.seen.add(event_reference_request)

    def get(self, object_id: int) -> Optional[EventReferenceRequestAggregate]:
        event_reference_request = self._get(object_id)
        if event_reference_request:
            self.seen.add(event_reference_request)
        return event_reference_request

    def remove(self, event_reference_request: EventReferenceRequestAggregate):
        self._remove(event_reference_request)
        self.seen.add(event_reference_request)

    @abc.abstractmethod
    def _add(
        self, event_reference_request: EventReferenceRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(
        self, event_reference_request: EventReferenceRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[EventReferenceRequestAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(
        self, event_reference_request: EventReferenceRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError
