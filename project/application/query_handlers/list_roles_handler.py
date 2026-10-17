from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_user_admin_read_repository import (
    AbstractUserAdminReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class ListRolesHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractUserAdminReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListRolesQuery):
        self.authz.ensure_is_platform_admin(query.actor)
        return self.repo.list_roles()
