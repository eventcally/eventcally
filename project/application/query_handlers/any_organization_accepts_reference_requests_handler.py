from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)


class AnyOrganizationAcceptsReferenceRequestsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAccessReadRepository):
        self.repo = repo

    def handle(self, query: queries.AnyOrganizationAcceptsReferenceRequestsQuery):
        return self.repo.any_accepts_reference_requests(query.exclude_admin_unit_id)
