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


class ListUserMemberInvitationsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationMemberInvitationReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListUserMemberInvitationsQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.list_for_user(query)
