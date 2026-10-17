import abc
from typing import List, Optional

from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.queries.list_event_dates_query import ListEventDatesQuery
from project.application.queries.list_events_query import ListEventsQuery
from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import (
    EventDateListItemReadModel,
    EventDateSearchHitReadModel,
    EventListItemReadModel,
    EventSearchItemReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractEventSearchReadRepository(abc.ABC):
    """Event and event-date searches and lists.

    The handler resolves what the actor may see (`can_read_private_events`,
    `can_read_planned_events`) and passes it in as facts.
    """

    @abc.abstractmethod
    def search_event_dates(
        self,
        criteria: EventSearchCriteria,
        page_request: PageRequest,
        can_read_private_events: bool,
        can_read_planned_events: bool,
        reference_admin_unit_id: Optional[ObjectId],
    ) -> Page[EventDateSearchHitReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def search_events(
        self,
        criteria: EventSearchCriteria,
        page_request: PageRequest,
        can_read_private_events: bool,
        can_read_planned_events: bool,
        reference_admin_unit_id: Optional[ObjectId],
        include_counts: bool = False,
    ) -> Page[EventSearchItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def organization_exists(self, admin_unit_id: ObjectId) -> bool:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_events(
        self, query: ListEventsQuery, can_read_private_events: bool
    ) -> Page[EventListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_event_dates(
        self, query: ListEventDatesQuery
    ) -> Page[EventDateListItemReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_events_for_search(
        self,
        criteria: EventSearchCriteria,
        can_read_private_events: bool,
        can_read_planned_events: bool,
    ) -> List[EventSearchItemReadModel]:  # pragma: no cover
        """Every match, unpaged."""
        raise NotImplementedError
