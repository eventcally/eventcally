from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_event_search_read_repository import (
    AbstractEventSearchReadRepository,
)
from project.application.services.event_visibility_service import EventVisibilityService


class ListEventsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventSearchReadRepository,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.visibility = visibility

    def handle(self, query: queries.ListEventsQuery):
        if query.admin_unit_id is not None and not self.repo.organization_exists(
            query.admin_unit_id
        ):
            return None

        can_read_private_events = bool(
            query.include_private
            and query.admin_unit_id is not None
            and self.visibility.can_read_private_events(
                query.actor, query.admin_unit_id
            )
        )
        return self.repo.list_events(query, can_read_private_events)
