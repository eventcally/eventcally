from typing import Optional

from project.domain.models.aggregates.calendar_entry_aggregate import (
    CalendarEntryAggregate,
)
from project.domain.repositories.abstract_calendar_entry_repository import (
    AbstractCalendarEntryRepository,
)
from project.infrastructure.models.calendar import Calendar
from project.infrastructure.models.calendar_entry import CalendarEntry
from project.infrastructure.sql_error_translation import flush


class SqlAlchemyCalendarEntryRepository(AbstractCalendarEntryRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, entry: CalendarEntryAggregate):
        model = CalendarEntry.from_aggregate(entry)
        self.session.add(model)
        flush(self.session)

        entry.id = model.id

    def _get_model(self, object_id: int) -> Optional[CalendarEntry]:
        return self.session.query(CalendarEntry).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[CalendarEntryAggregate]:
        model = self._get_model(object_id)
        return CalendarEntry.to_aggregate(model) if model else None

    def _get_by_calendar_and_event(
        self, calendar_id: int, event_id: int
    ) -> Optional[CalendarEntryAggregate]:
        model = (
            self.session.query(CalendarEntry)
            .filter_by(calendar_id=calendar_id, event_id=event_id)
            .first()
        )
        return CalendarEntry.to_aggregate(model) if model else None

    def _get_by_event_and_admin_unit(
        self, event_id: int, admin_unit_id: int
    ) -> list[CalendarEntryAggregate]:
        models = (
            self.session.query(CalendarEntry)
            .join(Calendar, Calendar.id == CalendarEntry.calendar_id)
            .filter(
                CalendarEntry.event_id == event_id,
                Calendar.admin_unit_id == admin_unit_id,
            )
            .all()
        )
        return [CalendarEntry.to_aggregate(model) for model in models]

    def _remove(self, entry: CalendarEntryAggregate):
        model = self._get_model(entry.id)
        self.session.delete(model)
