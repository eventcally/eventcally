from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_search_read_repository import (
    AbstractEventSearchReadRepository,
)


class ListEventDatesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventSearchReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventDatesQuery):
        return self.repo.list_event_dates(query)
