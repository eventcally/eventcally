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


class GetCalendarHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractCalendarReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.GetCalendarQuery):
        calendar = self.repo.get(query.id)

        if calendar is None:
            return None

        if calendar.private and not self.authz.has_permission_for_admin_unit(
            query.actor, calendar.admin_unit_id, "calendars:read"
        ):
            return None

        return calendar
