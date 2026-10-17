from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class GetEventPlaceRefHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventPlaceReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetEventPlaceRefQuery):
        return self.repo.get_ref(query.admin_unit_id, query.id)
