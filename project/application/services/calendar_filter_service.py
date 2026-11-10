from typing import List, Optional

from project.application.read_repositories.abstract_calendar_read_repository import (
    AbstractCalendarReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import NotFoundError
from project.domain.models.entities.actor import Actor
from project.domain.translation import dummy_gettext
from project.domain.types.object_id import ObjectId


class CalendarFilterService:
    """Who may filter an event search by a calendar: everybody for public calendars,
    only members with `calendars:read` for private ones. A missing and a hidden
    calendar answer the same, so the filter reveals nothing."""

    def __init__(
        self, repo: AbstractCalendarReadRepository, authz: ActorAuthorizationService
    ):
        self.repo = repo
        self.authz = authz

    def ensure_can_filter(self, actor: Optional[Actor], calendar_ids: List[ObjectId]):
        if not calendar_ids:
            return

        infos = {info.id: info for info in self.repo.get_filter_infos(calendar_ids)}

        for calendar_id in calendar_ids:
            info = infos.get(calendar_id)

            if info is None or (
                info.private
                and not self.authz.has_permission_for_admin_unit(
                    actor, info.admin_unit_id, "calendars:read"
                )
            ):
                raise NotFoundError(dummy_gettext("Calendar not found"))
