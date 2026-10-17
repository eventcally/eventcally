from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.application.services.event_visibility_service import EventVisibilityService


class GetEventDetailHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventDetailReadRepository,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.visibility = visibility

    def handle(self, query: queries.GetEventDetailQuery):
        visibility = self.repo.get_visibility(query.id)

        if visibility is None:
            return None

        self.visibility.ensure_can_read(query.actor, visibility)
        detail = self.repo.get_detail(query.id, query.reference_admin_unit_id)

        if detail is None:  # pragma: no cover
            return None

        return self.visibility.redact_detail(query.actor, detail)
