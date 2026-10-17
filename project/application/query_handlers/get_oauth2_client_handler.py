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

_PERMISSION = "oauth2_clients:read"


class GetOAuth2ClientHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOAuth2ClientReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetOAuth2ClientQuery):
        client = self.repo.get(query.id)

        if client is None:
            return None

        if client.admin_unit_id is not None:
            self.authz.ensure_permission_for_admin_unit(
                query.actor, client.admin_unit_id, _PERMISSION
            )
        else:
            self.authz.ensure_is_user(query.actor, client.user_id)

        return client
