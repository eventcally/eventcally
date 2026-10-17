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


class ListUserOAuth2TokensHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractOAuth2TokenReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListUserOAuth2TokensQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.list(query)
