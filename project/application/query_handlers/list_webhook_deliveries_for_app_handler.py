from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_child_read_repository import (
    AbstractAppChildReadRepository,
)


class ListWebhookDeliveriesForAppHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAppChildReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListWebhookDeliveriesForAppQuery):
        return self.repo.list_deliveries_for_app(query)
