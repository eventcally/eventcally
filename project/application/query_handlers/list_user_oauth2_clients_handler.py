from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_oauth2_client_read_repository import (
    AbstractOAuth2ClientReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class ListUserOAuth2ClientsHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractOAuth2ClientReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListUserOAuth2ClientsQuery):
        self.authz.ensure_is_user(query.actor, query.user_id)
        return self.repo.list(query)
