from datetime import date
from typing import List

from project.application.queries.base import Query
from project.application.read_models.external_calendar_read_models import (
    ExternalCalendarEventReadModel,
)


class ListExternalCalendarEventsQuery(Query[List[ExternalCalendarEventReadModel]]):
    """Planners only. `url` must be one of the configured planning calendars."""

    url: str
    date_from: date
    date_to: date
