from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.event_read_models import EventListItemReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListEventsQuery(Query[Optional[Page[EventListItemReadModel]]]):
    """Public events (published, verified organization), ordered by sort, then first
    start. With `admin_unit_id` the events of that organization; `None` if it does not
    exist."""

    admin_unit_id: Optional[ObjectId] = None
    # With `admin_unit_id`: also drafts and planned events, for actors with
    # `events:read` there.
    include_private: bool = False
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
