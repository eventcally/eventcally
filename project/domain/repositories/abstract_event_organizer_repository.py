import abc
from typing import Optional, Set

from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)


class AbstractEventOrganizerRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventOrganizerAggregate] = set()

    def add(self, event_organizer: EventOrganizerAggregate):
        self._add(event_organizer)
        self.seen.add(event_organizer)

    def update(self, event_organizer: EventOrganizerAggregate):
        self._update(event_organizer)
        self.seen.add(event_organizer)

    def get(self, object_id: int) -> Optional[EventOrganizerAggregate]:
        event_organizer = self._get(object_id)
        if event_organizer:
            self.seen.add(event_organizer)
        return event_organizer

    def remove(self, event_organizer: EventOrganizerAggregate):
        self._remove(event_organizer)
        self.seen.add(event_organizer)

    @abc.abstractmethod
    def _add(self, event_organizer: EventOrganizerAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, event_organizer: EventOrganizerAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[EventOrganizerAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event_organizer: EventOrganizerAggregate):  # pragma: no cover
        raise NotImplementedError
