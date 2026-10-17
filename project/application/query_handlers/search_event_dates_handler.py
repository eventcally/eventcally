from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.query_handlers.event_search_visibility import (
    can_read_planned_events,
    can_read_private_events,
)
from project.application.read_repositories.abstract_event_search_read_repository import (
    AbstractEventSearchReadRepository,
)
from project.application.services.event_visibility_service import EventVisibilityService


class SearchEventDatesHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventSearchReadRepository,
        visibility: EventVisibilityService,
    ):
        self.repo = repo
        self.visibility = visibility

    def handle(self, query: queries.SearchEventDatesQuery):
        criteria = query.criteria
        page = self.repo.search_event_dates(
            criteria,
            query.page,
            can_read_private_events(self.visibility, query.actor, criteria),
            can_read_planned_events(self.visibility, query.actor, criteria),
            query.reference_admin_unit_id,
        )
        events = self.visibility.redact_internal_tags(
            query.actor, [hit.event for hit in page.items]
        )
        items = [
            hit.model_copy(update={"event": event})
            for hit, event in zip(page.items, events)
        ]
        return page.model_copy(update={"items": items})
