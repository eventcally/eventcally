from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_admin_read_repository import (
    AbstractOrganizationAdminReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetOrganizationForAdminHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationAdminReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetOrganizationForAdminQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_is_platform_admin(query.actor)
        return result
