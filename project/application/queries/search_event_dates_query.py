from typing import Optional

from project.application.queries.base import Query
from project.application.queries.event_search_criteria import EventSearchCriteria
from project.application.queries.page_request import PageRequest
from project.application.read_models.event_read_models import (
    EventDateSearchHitReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class SearchEventDatesQuery(Query[Page[EventDateSearchHitReadModel]]):
    """One page of event dates, ordered by the sort, then by start."""

    criteria: EventSearchCriteria = EventSearchCriteria()
    # Fills `reference_id` of the events the organization references.
    reference_admin_unit_id: Optional[ObjectId] = None
    page: PageRequest = PageRequest()
