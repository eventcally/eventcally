import abc
from typing import Set

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

    @abc.abstractmethod
    def _get_by_event_id(
        self, event_id: int
    ) -> list[EventReferenceAggregate]:  # pragma: no cover
        raise NotImplementedError
