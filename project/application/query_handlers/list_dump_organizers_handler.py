from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_batch_read_repository import (
    AbstractBatchReadRepository,
)


class ListDumpOrganizersHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractBatchReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListDumpOrganizersQuery):
        return self.repo.list_dump_organizers(query)
