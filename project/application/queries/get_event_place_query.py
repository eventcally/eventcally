from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_place_read_models import (
    EventPlaceDetailReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventPlaceQuery(Query[Optional[EventPlaceDetailReadModel]]):
    id: ObjectId
