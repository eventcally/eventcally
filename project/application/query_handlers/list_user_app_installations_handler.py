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


class ListUserAppInstallationsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractAppInstallationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListUserAppInstallationsQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.list_for_user(query)
