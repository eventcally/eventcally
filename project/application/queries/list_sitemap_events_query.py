from typing import List

from project.application.queries.base import Query
from project.application.read_models.batch_read_models import SitemapEventReadModel


class ListSitemapEventsQuery(Query[List[SitemapEventReadModel]]):
    """Published events of verified organizations with a date from today on."""

    pass
