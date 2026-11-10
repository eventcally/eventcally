from typing import List

from project.application.queries.base import Query
from project.application.read_models.calendar_read_models import CalendarRefReadModel
from project.domain.types.object_id import ObjectId


class ListPublicCalendarsForEventQuery(Query[List[CalendarRefReadModel]]):
    """The public calendars of *other* organizations that contain the event. Only for
    actors with `events:read` on the event's organization, `[]` for everybody else."""

    event_id: ObjectId
