from typing import List

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ListEventCalendarIdsQuery(Query[List[ObjectId]]):
    """The ids of the organization's calendars that contain the event (prefills the
    calendar picker). Needs `calendars:read` on the organization."""

    admin_unit_id: ObjectId
    event_id: ObjectId
