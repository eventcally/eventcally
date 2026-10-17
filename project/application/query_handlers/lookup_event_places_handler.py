from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class LookupEventPlacesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventPlaceReadRepository):
        self.repo = repo

    def handle(self, query: queries.LookupEventPlacesQuery):
        return self.repo.lookup(query)
