import abc
from typing import Set

from project.models.event_place import EventPlace


class AbstractEventPlaceRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventPlace] = set()

    def add(self, event_place: EventPlace):
        self._add(event_place)
        self.seen.add(event_place)

    def get(self, object_id: int) -> EventPlace:
        event_place = self._get(object_id)
        if event_place:
            self.seen.add(event_place)
        return event_place

    def remove(self, event_place: EventPlace):
        self._remove(event_place)
        self.seen.add(event_place)

    @abc.abstractmethod
    def _add(self, event_place: EventPlace):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> EventPlace:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event_place: EventPlace):  # pragma: no cover
        raise NotImplementedError
