import abc
from typing import Optional

from project.application.queries.list_calendars_query import ListCalendarsQuery
from project.application.read_models.calendar_read_models import (
    CalendarListItemReadModel,
    CalendarReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractCalendarReadRepository(abc.ABC):
    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list(
        self, query: ListCalendarsQuery, include_private: bool
    ) -> Page[CalendarListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get(
        self, object_id: ObjectId
    ) -> Optional[CalendarReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:  # pragma: no cover
        raise NotImplementedError
