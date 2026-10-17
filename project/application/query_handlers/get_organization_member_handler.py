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

_READ_PERMISSION = "organization_members:read"


class GetOrganizationMemberHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractOrganizationMemberReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetOrganizationMemberQuery):
        member = self.repo.get(query.id)

        if member is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, member.admin_unit_id, _READ_PERMISSION
        )
        return member
