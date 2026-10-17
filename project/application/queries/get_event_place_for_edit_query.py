from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_place_read_models import (
    EventPlaceEditReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventPlaceForEditQuery(Query[Optional[EventPlaceEditReadModel]]):
    """`None` if the place does not exist. Fills the manage update form and backs the
    delete confirmation."""

    id: ObjectId
