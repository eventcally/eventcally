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


class GetUserOrganizationInvitationHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationInvitationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetUserOrganizationInvitationQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_is_recipient(query.actor, result.email)
        return result
