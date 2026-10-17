from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)


class GetEventCategoryByNameQuery(Query[Optional[EventCategoryRefReadModel]]):
    """The event category with exactly this name, or `None`."""

    name: str
