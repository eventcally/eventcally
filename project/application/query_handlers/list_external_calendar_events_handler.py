import json

from project.application import queries
from project.application.query_handlers.abstract_query_handler import (
    AbstractQueryHandler,
)
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.application.services.abstract_external_calendar_reader import (
    AbstractExternalCalendarReader,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError


class ListExternalCalendarEventsHandler(AbstractQueryHandler):
    def __init__(
        self,
        settings_repo: AbstractSiteSettingsReadRepository,
        reader: AbstractExternalCalendarReader,
        authz: ActorAuthorizationService,
    ):
        self.settings_repo = settings_repo
        self.reader = reader
        self.authz = authz

    def handle(self, query: queries.ListExternalCalendarEventsQuery):
        if not self.authz.can_use_planning(query.actor):
            raise UnauthorizedError()

        # Only configured URLs are fetched: this must not become an open proxy.
        if query.url not in self._configured_urls():
            raise UnauthorizedError()

        return self.reader.list_events(query.url, query.date_from, query.date_to)

    def _configured_urls(self) -> set:
        raw = self.settings_repo.get_settings().planning_external_calendars
        try:
            calendars = json.loads(raw) if raw else []
            return {c["url"] for c in calendars}
        except (ValueError, TypeError, KeyError):
            return set()
