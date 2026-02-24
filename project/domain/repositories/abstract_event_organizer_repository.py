import abc
from typing import Set

from project.models.event_organizer import EventOrganizer


class AbstractEventOrganizerRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[EventOrganizer] = set()

    def add(self, event_organizer: EventOrganizer):
        self._add(event_organizer)
        self.seen.add(event_organizer)

    def get(self, object_id: int) -> EventOrganizer:
        event_organizer = self._get(object_id)
        if event_organizer:
            self.seen.add(event_organizer)
        return event_organizer

    def remove(self, event_organizer: EventOrganizer):
        self._remove(event_organizer)
        self.seen.add(event_organizer)

    @abc.abstractmethod
    def _add(self, event_organizer: EventOrganizer):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> EventOrganizer:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, event_organizer: EventOrganizer):  # pragma: no cover
        raise NotImplementedError
