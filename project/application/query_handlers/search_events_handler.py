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
from project.application.services.calendar_filter_service import CalendarFilterService
from project.application.services.event_visibility_service import EventVisibilityService


class SearchEventsHandler(AbstractQueryHandler):
    def __init__(
        self,
        repo: AbstractEventSearchReadRepository,
        visibility: EventVisibilityService,
        calendar_filter: CalendarFilterService,
    ):
        self.repo = repo
        self.visibility = visibility
        self.calendar_filter = calendar_filter

    def handle(self, query: queries.SearchEventsQuery):
        criteria = query.criteria
        self.calendar_filter.ensure_can_filter(query.actor, criteria.calendar_ids)
        page = self.repo.search_events(
            criteria,
            query.page,
            can_read_private_events(self.visibility, query.actor, criteria),
            can_read_planned_events(self.visibility, query.actor, criteria),
            query.reference_admin_unit_id,
            query.include_counts,
        )
        items = self.visibility.redact_internal_tags(query.actor, page.items)
        return page.model_copy(update={"items": items})
