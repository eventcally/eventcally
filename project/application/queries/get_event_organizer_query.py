from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerDetailReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventOrganizerQuery(Query[Optional[EventOrganizerDetailReadModel]]):
    id: ObjectId
