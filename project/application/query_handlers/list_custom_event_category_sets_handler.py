from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_reference_data_read_repository import (
    AbstractReferenceDataReadRepository,
)


class ListCustomEventCategorySetsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractReferenceDataReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListCustomEventCategorySetsQuery):
        return self.repo.list_custom_event_category_sets(query)
