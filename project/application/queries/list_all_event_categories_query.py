from typing import List

from project.application.queries.base import Query
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)


class ListAllEventCategoriesQuery(Query[List[EventCategoryRefReadModel]]):
    """Every event category (the select2 loader sorts and pages by localized name)."""

    pass
