from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)


class GetSiteNoticesHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractSiteSettingsReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetSiteNoticesQuery):
        return self.repo.get_site_notices()
