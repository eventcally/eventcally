from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.page import Page
from project.application.read_models.reference_data_read_models import (
    EventCategoryRefReadModel,
)


class ListEventCategoriesQuery(Query[Page[EventCategoryRefReadModel]]):
    """All event categories in id order (public)."""

    page: PageRequest = PageRequest()
