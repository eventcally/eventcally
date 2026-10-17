from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_organizer_read_repository import (
    AbstractEventOrganizerReadRepository,
)


class GetEventOrganizerForEditHandler(AbstractQueryHandler):
    """No actor authorization: organizer data is public, the manage views are gated by
    their permission decorator and the owner check, and the command re-checks."""

    def __init__(self, repo: AbstractEventOrganizerReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetEventOrganizerForEditQuery):
        return self.repo.get_for_edit(query.id)
