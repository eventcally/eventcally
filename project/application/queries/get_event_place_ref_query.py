from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_place_read_models import (
    EventPlaceSuggestionReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventPlaceRefQuery(Query[Optional[EventPlaceSuggestionReadModel]]):
    """The place if it belongs to the organization, else `None`."""

    admin_unit_id: ObjectId
    id: ObjectId
