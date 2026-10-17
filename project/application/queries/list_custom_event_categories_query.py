from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.reference_data_read_models import (
    CustomEventCategoryRefReadModel,
)
from project.domain.types.object_id import ObjectId


class ListCustomEventCategoriesQuery(Query[Page[CustomEventCategoryRefReadModel]]):
    """The categories of a custom category set in id order (public); an unknown
    set yields an empty page."""

    category_set_id: ObjectId
    page: PageRequest = PageRequest()
