from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)


class ListEventCalendarIdsHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractCalendarReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListEventCalendarIdsQuery):
        self.authz.ensure_permission_for_admin_unit(
            query.actor, query.admin_unit_id, "calendars:read"
        )
        return self.repo.list_calendar_ids_of_event(query.admin_unit_id, query.event_id)
