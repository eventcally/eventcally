from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)


class ListUpcomingEventDatesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventDetailReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListUpcomingEventDatesQuery):
        return self.repo.list_upcoming_dates(query.event_id)
