from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_reference_data_read_repository import (
    AbstractReferenceDataReadRepository,
)


class ListEventCategoriesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractReferenceDataReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListEventCategoriesQuery):
        return self.repo.list_event_categories(query)
