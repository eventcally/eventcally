from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class ListEventPlaceSuggestionsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventPlaceReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventPlaceSuggestionsQuery):
        return self.repo.list_suggestions(query)
