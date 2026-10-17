from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_api_key_read_repository import (
    AbstractApiKeyReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "api_keys:read"


class GetApiKeyHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractApiKeyReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetApiKeyQuery):
        api_key = self.repo.get(query.id)

        if api_key is None:
            return None

        if api_key.admin_unit_id is not None:
            self.authz.ensure_permission_for_admin_unit(
                query.actor, api_key.admin_unit_id, _PERMISSION
            )
        else:
            self.authz.ensure_is_user(query.actor, api_key.user_id)

        return api_key
