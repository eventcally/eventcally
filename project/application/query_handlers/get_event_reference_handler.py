from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_reference_read_repository import (
    AbstractEventReferenceReadRepository,
)


class GetEventReferenceHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractEventReferenceReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetEventReferenceQuery):
        return self.repo.get(query.id)
