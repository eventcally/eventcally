from typing import List

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import SitemapCalendarReadModel


class ListSitemapCalendarsQuery(Query[List[SitemapCalendarReadModel]]):
    """The public (not private) calendars."""

    pass
