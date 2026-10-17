from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)


class GetInstallableAppHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractAppInstallationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetInstallableAppQuery):
        return self.repo.get_installable_app(query.id)
