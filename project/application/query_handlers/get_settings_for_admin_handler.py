from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetSettingsForAdminHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractSiteSettingsReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetSettingsForAdminQuery):
        self.authz.ensure_is_platform_admin(query.actor)
        return self.repo.get_settings()
