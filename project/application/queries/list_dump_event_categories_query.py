from typing import List

from project.application.queries.base import Query
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)


class ListDumpEventCategoriesQuery(Query[List[EventCategoryRefReadModel]]):
    """Every event category (a few dozen) for the data dumps."""

    pass
