from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_read_repository import (
    AbstractOrganizationReadRepository,
)


class GetOrganizationHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractOrganizationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetOrganizationQuery):
        return self.repo.get(query.id)
