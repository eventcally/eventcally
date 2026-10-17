from typing import Optional

from pydantic import Field

from project.application.queries.base import Query
from project.application.read_models.event_place_read_models import (
    EventPlaceSuggestionReadModel,
)
from project.domain.types.object_id import ObjectId


class ListEventPlaceSuggestionsQuery(Query[list[EventPlaceSuggestionReadModel]]):
    """Autocomplete: places matching `keyword` anywhere, prefix matches first."""

    admin_unit_id: ObjectId
    keyword: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=50)
