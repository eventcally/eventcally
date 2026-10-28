from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_verification_request_read_repository import (
    AbstractOrganizationVerificationRequestReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "incoming_organization_verification_requests:read"


class GetIncomingOrganizationVerificationRequestHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationVerificationRequestReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetIncomingOrganizationVerificationRequestQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, result.target_admin_unit_id, _PERMISSION
        )
        return result
