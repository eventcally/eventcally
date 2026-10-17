from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_custom_widget_read_repository import (
    AbstractCustomWidgetReadRepository,
)


class GetCustomWidgetHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractCustomWidgetReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetCustomWidgetQuery):
        return self.repo.get(query.id)
