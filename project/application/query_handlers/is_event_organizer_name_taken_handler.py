from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_organizer_read_repository import (
    AbstractEventOrganizerReadRepository,
)


class IsEventOrganizerNameTakenHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventOrganizerReadRepository):
        self.repo = repo

    def handle(self, query: queries.IsEventOrganizerNameTakenQuery):
        return self.repo.is_name_taken(
            query.admin_unit_id, query.name, exclude_id=query.exclude_id
        )
