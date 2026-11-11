from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.calendar_read_models import CalendarReadModel
from project.domain.types.object_id import ObjectId


class GetCalendarQuery(Query[Optional[CalendarReadModel]]):
    """A calendar, or `None` if it does not exist or is private and the actor has no
    `calendars:read` on its organization (a private calendar is never revealed)."""

    id: ObjectId
