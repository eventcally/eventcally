from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.reference_data_read_models import (
    CustomEventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class GetCustomEventCategoryQuery(Query[Optional[CustomEventCategoryRefReadModel]]):
    """The custom event category, or `None`."""

    id: ObjectId
