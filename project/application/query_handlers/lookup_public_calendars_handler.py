from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)


class LookupPublicCalendarsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractCalendarReadRepository):
        self.repo = repo

    def handle(self, query: queries.LookupPublicCalendarsQuery):
        return self.repo.lookup_public(query.keyword.strip(), query.limit)
