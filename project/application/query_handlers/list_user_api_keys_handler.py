from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_api_key_read_repository import (
    AbstractApiKeyReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class ListUserApiKeysHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractApiKeyReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListUserApiKeysQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.list(query)
