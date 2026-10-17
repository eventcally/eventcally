from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_read_models import EventDateDetailReadModel
from project.domain.types.object_id import ObjectId


class GetEventDateDetailQuery(Query[Optional[EventDateDetailReadModel]]):
    """The event date with its event; `None` if unknown. Authorizes like `GetEventDetailQuery`."""

    id: ObjectId
