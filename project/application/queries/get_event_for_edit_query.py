from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_read_models import EventEditReadModel
from project.domain.types.object_id import ObjectId


class GetEventForEditQuery(Query[Optional[EventEditReadModel]]):
    """The event for the manage update form, delete confirmation and "use as
    template"; `None` if unknown. Raises `UnauthorizedError` unless the actor may
    read the event; the views additionally check ownership."""

    id: ObjectId
