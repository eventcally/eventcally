from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_detail_read_repository import (
    AbstractEventDetailReadRepository,
)
from project.application.services.event_visibility_service import EventVisibilityService


class ListEventDatesOfEventHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventDetailReadRepository,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.visibility = visibility

    def handle(self, query: queries.ListEventDatesOfEventQuery):
        visibility = self.repo.get_visibility(query.event_id)

        if visibility is None:
            return None

        self.visibility.ensure_can_read(query.actor, visibility)
        return self.repo.list_dates_of_event(query.event_id, query.page)
