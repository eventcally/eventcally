from typing import List

from project.application.queries.base import Query
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.read_models.event_read_models import EventSearchItemReadModel


class ListAllEventsQuery(Query[List[EventSearchItemReadModel]]):
    """Every event the search finds (no paging): the iCal feeds and bulk jobs."""

    criteria: EventSearchCriteria = EventSearchCriteria()
