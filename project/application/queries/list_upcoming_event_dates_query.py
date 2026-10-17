from typing import List

from project.application.queries.base import Query
from project.application.read_models.event_read_models import EventDateReadModel
from project.domain.types.object_id import ObjectId


class ListUpcomingEventDatesQuery(Query[List[EventDateReadModel]]):
    """The dates of an event starting today or later, by start. No authorization: callers have read the event."""

    event_id: ObjectId
