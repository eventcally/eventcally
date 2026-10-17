from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.reference_data_read_models import (
    CustomEventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class LookupCustomEventCategoriesQuery(Query[Page[CustomEventCategoryRefReadModel]]):
    """Select2 lookup: categories of a set whose name or label match `term`, by name, label."""

    category_set_id: ObjectId
    term: Optional[str] = None
    page: PageRequest = PageRequest()
