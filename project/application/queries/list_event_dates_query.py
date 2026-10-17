from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.event_read_models import EventDateListItemReadModel
from project.application.read_models.page import Page


class ListEventDatesQuery(Query[Page[EventDateListItemReadModel]]):
    """Dates of public events (published, verified organization), ordered by sort, then start."""

    # Bounds and sort apply to the owning event's audit columns, as the legacy list.
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
