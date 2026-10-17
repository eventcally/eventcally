from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_oauth2_token_read_repository import (
    AbstractOAuth2TokenReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class GetUserOAuth2TokenHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractOAuth2TokenReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetUserOAuth2TokenQuery):
        result = self.repo.get(query.id)

        if result is None:
            return None

        self.authz.ensure_is_user(query.actor, result.user_id)
        return result
