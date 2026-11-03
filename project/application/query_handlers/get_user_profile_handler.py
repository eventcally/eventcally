from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_user_profile_read_repository import (
    AbstractUserProfileReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetUserProfileHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractUserProfileReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetUserProfileQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.get_profile(query.user_id)
