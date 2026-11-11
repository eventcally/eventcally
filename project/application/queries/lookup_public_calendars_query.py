from typing import List

from pydantic import Field

from project.application.queries.base import Query
from project.application.read_models.calendar_read_models import CalendarRefReadModel


class LookupPublicCalendarsQuery(Query[List[CalendarRefReadModel]]):
    """Public (not private) calendars of verified organizations whose name or whose
    organization's name contains `keyword`, for the calendar filter of the public
    event date search."""

    keyword: str = ""
    limit: int = Field(default=10, ge=1, le=50)
