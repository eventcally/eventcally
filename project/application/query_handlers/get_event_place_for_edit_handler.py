from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_place_read_repository import (
    AbstractEventPlaceReadRepository,
)


class GetEventPlaceForEditHandler(AbstractQueryHandler):
    """No actor authorization: place data is public, the manage views are gated by
    their permission decorator and the owner check, and the command re-checks."""

    def __init__(self, repo: AbstractEventPlaceReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetEventPlaceForEditQuery):
        return self.repo.get_for_edit(query.id)
