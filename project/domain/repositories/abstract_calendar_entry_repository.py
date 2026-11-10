import abc
from typing import Optional, Set

from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)


class AbstractCalendarEntryRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[CalendarEntryAggregate] = set()

    def add(self, entry: CalendarEntryAggregate):
        self._add(entry)
        self.seen.add(entry)

    def get_by_calendar_and_event(
        self, calendar_id: int, event_id: int
    ) -> Optional[CalendarEntryAggregate]:
        entry = self._get_by_calendar_and_event(calendar_id, event_id)
        if entry:
            self.seen.add(entry)
        return entry

    def get_by_event_and_admin_unit(
        self, event_id: int, admin_unit_id: int
    ) -> list[CalendarEntryAggregate]:
        """The entries of the event in calendars of the organization."""
        entries = self._get_by_event_and_admin_unit(event_id, admin_unit_id)
        self.seen.update(entries)
        return entries

    def get(self, object_id: int) -> Optional[CalendarEntryAggregate]:
        entry = self._get(object_id)
        if entry:
            self.seen.add(entry)
        return entry

    def remove(self, entry: CalendarEntryAggregate):
        self._remove(entry)
        self.seen.add(entry)

    @abc.abstractmethod
    def _add(self, entry: CalendarEntryAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[CalendarEntryAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_calendar_and_event(
        self, calendar_id: int, event_id: int
    ) -> Optional[CalendarEntryAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_event_and_admin_unit(
        self, event_id: int, admin_unit_id: int
    ) -> list[CalendarEntryAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, entry: CalendarEntryAggregate):  # pragma: no cover
        raise NotImplementedError
