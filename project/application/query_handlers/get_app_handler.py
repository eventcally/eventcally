from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_oauth2_client_read_repository import (
    AbstractOAuth2ClientReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "apps:read"


class GetAppHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractOAuth2ClientReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetAppQuery):
        result = self.repo.get_app(query.id)

        if result is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, result.admin_unit_id, _PERMISSION
        )
        return result
