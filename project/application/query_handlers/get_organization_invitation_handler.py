from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_invitation_read_repository import (
    AbstractOrganizationInvitationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_READ_PERMISSION = "organization_invitations:read"


class GetOrganizationInvitationHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationInvitationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetOrganizationInvitationQuery):
        detail = self.repo.get(query.id)

        if detail is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, detail.admin_unit_id, _READ_PERMISSION
        )
        return detail
