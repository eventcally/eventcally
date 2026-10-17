from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_batch_read_repository import (
    AbstractBatchReadRepository,
)


class ListUserIdsDueForDeletionHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractBatchReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListUserIdsDueForDeletionQuery):
        return self.repo.list_user_ids_due_for_deletion()
