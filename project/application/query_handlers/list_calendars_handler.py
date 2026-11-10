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


class ListCalendarsHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractCalendarReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListCalendarsQuery):
        if not self.repo.organization_exists(query.admin_unit_id):
            return None

        include_private = self.authz.has_permission_for_admin_unit(
            query.actor, query.admin_unit_id, "calendars:read"
        )
        return self.repo.list(query, include_private)
