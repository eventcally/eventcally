import abc
from typing import Optional, Set

from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate


class AbstractCalendarRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[CalendarAggregate] = set()

    def add(self, calendar: CalendarAggregate):
        self._add(calendar)
        self.seen.add(calendar)

    def update(self, calendar: CalendarAggregate):
        self._update(calendar)
        self.seen.add(calendar)

    def get(self, object_id: int) -> Optional[CalendarAggregate]:
        calendar = self._get(object_id)
        if calendar:
            self.seen.add(calendar)
        return calendar

    def get_by_admin_unit_and_name(
        self, admin_unit_id: int, name: str
    ) -> Optional[CalendarAggregate]:
        """Case-insensitive lookup of the calendar name within an organization."""
        calendar = self._get_by_admin_unit_and_name(admin_unit_id, name)
        if calendar:
            self.seen.add(calendar)
        return calendar

    def remove(self, calendar: CalendarAggregate):
        self._remove(calendar)
        self.seen.add(calendar)

    @abc.abstractmethod
    def _add(self, calendar: CalendarAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, calendar: CalendarAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> Optional[CalendarAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_admin_unit_and_name(
        self, admin_unit_id: int, name: str
    ) -> Optional[CalendarAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, calendar: CalendarAggregate):  # pragma: no cover
        raise NotImplementedError
