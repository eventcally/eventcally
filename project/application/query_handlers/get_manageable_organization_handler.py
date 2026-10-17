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


class GetManageableOrganizationHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractAccessReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetManageableOrganizationQuery):
        actor = query.actor

        if actor is None or actor.user_id is None:
            return None

        if not self.authz.reader.is_platform_admin(
            actor.user_id
        ) and query.id not in self.repo.member_organization_ids(actor.user_id):
            return None

        return self.repo.get_organization(query.id)
