from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_access_read_repository import (
    AbstractAccessReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class ListManageableOrganizationsHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractAccessReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListManageableOrganizationsQuery):
        actor = query.actor

        if actor is None or actor.user_id is None:
            return []

        if not query.member_only and self.authz.reader.is_platform_admin(actor.user_id):
            return self.repo.list_organizations(None)

        return self.repo.list_organizations(
            self.repo.member_organization_ids(actor.user_id)
        )
