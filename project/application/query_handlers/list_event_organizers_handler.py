from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_organizer_read_repository import (
    AbstractEventOrganizerReadRepository,
)


class ListEventOrganizersHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventOrganizerReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventOrganizersQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        return self.repo.list(query)
