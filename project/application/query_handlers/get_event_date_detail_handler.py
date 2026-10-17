from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.application.services.event_visibility_service import EventVisibilityService


class GetEventDateDetailHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventDetailReadRepository,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.visibility = visibility

    def handle(self, query: queries.GetEventDateDetailQuery):
        visibility = self.repo.get_visibility_of_date(query.id)

        if visibility is None:
            return None

        self.visibility.ensure_can_read(query.actor, visibility)
        detail = self.repo.get_date_detail(query.id)

        if detail is None:  # pragma: no cover
            return None

        event = self.visibility.redact_detail(query.actor, detail.event)
        return detail.model_copy(update={"event": event})
