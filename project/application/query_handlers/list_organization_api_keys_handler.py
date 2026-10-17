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


class ListOrganizationApiKeysHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractApiKeyReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListOrganizationApiKeysQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, _PERMISSION
        )
        return self.repo.list(query)
