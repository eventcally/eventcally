from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.custom_widget_read_models import (
    CustomWidgetReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListCustomWidgetsQuery(Query[Optional[Page[CustomWidgetReadModel]]]):
    """Custom widgets of an organization by name; `name` matches `ILIKE %name%`.
    `None` if the organization does not exist. Requires `custom_widgets:read`."""

    admin_unit_id: ObjectId
    name: Optional[str] = None
    page: PageRequest = PageRequest()
