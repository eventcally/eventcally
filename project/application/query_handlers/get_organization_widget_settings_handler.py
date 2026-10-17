from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_read_repository import (
    AbstractOrganizationReadRepository,
)


class GetOrganizationWidgetSettingsHandler(AbstractQueryHandler):
    def __init__(self, repo: AbstractOrganizationReadRepository):
        self.repo = repo

    def handle(self, query: queries.GetOrganizationWidgetSettingsQuery):
        return self.repo.get_widget_settings(query.id)
