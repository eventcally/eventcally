from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)


class GetAppInstallationForAppHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAppInstallationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetAppInstallationForAppQuery):
        return self.repo.get_for_app(query.app_id, query.id)
