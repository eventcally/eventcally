from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)


class GetSettingsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractSiteSettingsReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetSettingsQuery):
        return self.repo.get_settings()
