from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)


class CanRequestVerificationHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAccessReadRepository):
        self.repo = repo

    def handle(self, query: queries.CanRequestVerificationQuery):
        return self.repo.can_request_verification(
            query.source_admin_unit_id, query.target_admin_unit_id
        )
