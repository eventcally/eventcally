from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_installation_read_repository import (
    AbstractAppInstallationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "app_installations:read"


class GetAppInstallationHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractAppInstallationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetAppInstallationQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, result.admin_unit_id, _PERMISSION
        )
        return result
