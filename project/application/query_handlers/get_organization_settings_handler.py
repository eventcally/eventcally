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
from project.domain.errors import UnauthorizedError


class GetOrganizationSettingsHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractAccessReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetOrganizationSettingsQuery):
        actor = query.actor

        if (
            actor is None
            or actor.user_id is None
            or (
                not self.authz.reader.is_platform_admin(actor.user_id)
                and query.id not in self.repo.member_organization_ids(actor.user_id)
            )
        ):
            raise UnauthorizedError(f"Actor does not manage organization {query.id}.")

        return self.repo.get_settings(query.id)
