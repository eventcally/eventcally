from enum import Enum
from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import TrackableCriteria
from project.application.read_models.calendar_read_models import (
    CalendarListItemReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class CalendarSort(str, Enum):
    """Values equal the API `sort` strings and the manage list sort keys."""

    name = "name"
    created_at_desc = "-created_at"
    updated_at_desc = "-updated_at"
    last_modified_at_desc = "-last_modified_at"
    number_of_events_desc = "-number_of_events"


class ListCalendarsQuery(Query[Optional[Page[CalendarListItemReadModel]]]):
    """Calendars of an organization; `None` if the organization does not exist.

    Private calendars are listed only for actors with `calendars:read` on the
    organization. `name` (API) matches anywhere and ranks prefix matches first.
    `keyword` (manage list) follows `parse_like_term`.
    """

    admin_unit_id: ObjectId
    name: Optional[str] = None
    keyword: Optional[str] = None
    sort: Optional[CalendarSort] = None
    trackable: TrackableCriteria = TrackableCriteria()
    page: PageRequest = PageRequest()
