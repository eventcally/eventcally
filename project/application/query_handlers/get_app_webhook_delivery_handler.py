from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_app_child_read_repository import (
    AbstractAppChildReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "webhook_deliveries:read"


class GetAppWebhookDeliveryHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractAppChildReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetAppWebhookDeliveryQuery):
        result = self.repo.get_delivery(query.id)

        if result is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, result.admin_unit_id, _PERMISSION
        )
        return result
