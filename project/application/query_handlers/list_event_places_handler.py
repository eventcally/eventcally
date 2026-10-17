from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class ListEventPlacesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventPlaceReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventPlacesQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        return self.repo.list(query)
