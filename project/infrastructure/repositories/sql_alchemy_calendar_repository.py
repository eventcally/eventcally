from typing import Optional

from sqlalchemy import func

from project.domain.models.aggregates.calendar_aggregate import CalendarAggregate
from project.domain.repositories.abstract_calendar_repository import (
    AbstractCalendarRepository,
)
from project.infrastructure.models.calendar import Calendar
from project.infrastructure.sql_error_translation import flush


class SqlAlchemyCalendarRepository(AbstractCalendarRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, calendar: CalendarAggregate):
        model = Calendar.from_aggregate(calendar)
        self.session.add(model)
        flush(self.session)

        calendar.id = model.id

    def _update(self, calendar: CalendarAggregate):
        model = self._get_model(calendar.id)
        model.fill_from_aggregate(calendar)
        self.session.merge(model)
        flush(self.session)

    def _get_model(self, object_id: int) -> Optional[Calendar]:
        return self.session.query(Calendar).filter_by(id=object_id).first()

    def _get(self, object_id: int) -> Optional[CalendarAggregate]:
        model = self._get_model(object_id)
        return Calendar.to_aggregate(model) if model else None

    def _get_by_admin_unit_and_name(
        self, admin_unit_id: int, name: str
    ) -> Optional[CalendarAggregate]:
        model = (
            self.session.query(Calendar)
            .filter(
                Calendar.admin_unit_id == admin_unit_id,
                func.lower(Calendar.name) == name.lower(),
            )
            .first()
        )
        return Calendar.to_aggregate(model) if model else None

    def _remove(self, calendar: CalendarAggregate):
        model = self._get_model(calendar.id)
        self.session.delete(model)
