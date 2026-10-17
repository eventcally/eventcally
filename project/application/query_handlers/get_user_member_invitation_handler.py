from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_member_invitation_read_repository import (
    AbstractOrganizationMemberInvitationReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetUserMemberInvitationHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationMemberInvitationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetUserMemberInvitationQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_is_recipient(query.actor, result.email)
        return result
