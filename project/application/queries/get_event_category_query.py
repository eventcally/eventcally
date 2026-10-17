from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventCategoryQuery(Query[Optional[EventCategoryRefReadModel]]):
    """The event category, or `None`."""

    id: ObjectId
