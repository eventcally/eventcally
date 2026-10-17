from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReviewReadModel,
)
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.application.read_repositories.abstract_event_reference_request_read_repository import (
    AbstractEventReferenceRequestReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.application.services.event_visibility_service import EventVisibilityService

_PERMISSION = "incoming_event_reference_requests:read"


class GetIncomingEventReferenceRequestReviewHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventReferenceRequestReadRepository,
        event_repo: AbstractEventDetailReadRepository,
        authz: ActorAuthorizationService,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.event_repo = event_repo
        self.authz = authz
        self.visibility = visibility

    def handle(self, query: queries.GetIncomingEventReferenceRequestReviewQuery):
        request = self.repo.get(query.id)

        if request is None:
            return None

        self.authz.ensure_permission_for_admin_unit(
            query.actor, request.admin_unit_id, _PERMISSION
        )
        event = self.event_repo.get_detail(request.event_id, None)

        if event is None:  # pragma: no cover
            return None

        event = self.visibility.redact_detail(query.actor, event)
        return EventReferenceRequestReviewReadModel(
            **{**dict(request), "event": event},
            upcoming_dates=self.event_repo.list_upcoming_dates(request.event_id),
            auto_verify=self.repo.auto_verifies(
                request.admin_unit_id, event.admin_unit_id
            ),
        )
