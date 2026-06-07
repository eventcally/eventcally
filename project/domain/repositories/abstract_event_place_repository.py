import abc
from typing import Optional, Set

from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate


class AbstractEventPlaceRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventPlaceAggregate] = set()

    def add(self, event_place: EventPlaceAggregate):
        self._add(event_place)
        self.seen.add(event_place)

    def update(self, event_place: EventPlaceAggregate):
        self._update(event_place)
        self.seen.add(event_place)

    def get(self, object_id: int) -> Optional[EventPlaceAggregate]:
        event_place = self._get(object_id)
        if event_place:
            self.seen.add(event_place)
        return event_place

    def remove(self, event_place: EventPlaceAggregate):
        self._remove(event_place)
        self.seen.add(event_place)

    @abc.abstractmethod
    def _add(self, event_place: EventPlaceAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> Optional[EventPlaceAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, event_place: EventPlaceAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event_place: EventPlaceAggregate):  # pragma: no cover
        raise NotImplementedError
