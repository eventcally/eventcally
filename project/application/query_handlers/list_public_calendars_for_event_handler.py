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


class ListPublicCalendarsForEventHandler(AbstractQueryHandler):
    def __init__(
        self, repo: AbstractCalendarReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def handle(self, query: queries.ListPublicCalendarsForEventQuery):
        admin_unit_id = self.repo.event_admin_unit_id(query.event_id)

        if admin_unit_id is None or not self.authz.has_permission_for_admin_unit(
            query.actor, admin_unit_id, "events:read"
        ):
            return []

        return self.repo.list_public_calendars_of_other_organizations(
            query.event_id, admin_unit_id
        )
