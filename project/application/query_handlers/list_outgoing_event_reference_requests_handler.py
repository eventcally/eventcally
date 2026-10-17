from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_reference_request_read_repository import (
    AbstractEventReferenceRequestReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)

_PERMISSION = "outgoing_event_reference_requests:read"


class ListOutgoingEventReferenceRequestsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventReferenceRequestReadRepository,
        authz: ActorAuthorizationService,
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListOutgoingEventReferenceRequestsQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, _PERMISSION
        )
        return self.repo.list_outgoing(query)
