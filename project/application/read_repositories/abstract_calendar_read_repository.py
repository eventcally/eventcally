import abc
from typing import List, Optional

from project.application.queries.list_calendars_query import ListCalendarsQuery
from project.application.read_models.calendar_read_models import (
    CalendarFilterInfo,
    CalendarListItemReadModel,
    CalendarReadModel,
    CalendarRefReadModel,
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
    def get_filter_infos(
        self, ids: List[ObjectId]
    ) -> List[CalendarFilterInfo]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def event_admin_unit_id(
        self, event_id: ObjectId
    ) -> Optional[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_calendar_ids_of_event(
        self, admin_unit_id: ObjectId, event_id: ObjectId
    ) -> List[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_public_calendars_of_other_organizations(
        self, event_id: ObjectId, admin_unit_id: ObjectId
    ) -> List[CalendarRefReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def is_name_taken(
        self,
        admin_unit_id: ObjectId,
        name: str,
        exclude_id: Optional[ObjectId] = None,
    ) -> bool:  # pragma: no cover
        raise NotImplementedError
