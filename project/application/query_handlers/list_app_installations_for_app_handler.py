from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)


class ListAppInstallationsForAppHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAppInstallationReadRepository):
        self.repo = repo

    def handle(self, query: queries.ListAppInstallationsForAppQuery):
        return self.repo.list_for_app(query)
