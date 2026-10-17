from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)


class GetCurrentOrganizationHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAccessReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetCurrentOrganizationQuery):
        return self.repo.get_organization(query.id)
