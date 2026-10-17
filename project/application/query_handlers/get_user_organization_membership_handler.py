from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_organization_member_read_repository import (
    AbstractOrganizationMemberReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetUserOrganizationMembershipHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationMemberReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetUserOrganizationMembershipQuery):
        membership = self.repo.get_membership(query.id)

        if membership is None:
            return None

        self.authz.ensure_is_user(query.actor, membership.user_id)
        return membership
