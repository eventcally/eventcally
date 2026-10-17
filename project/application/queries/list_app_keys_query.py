from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.app_child_read_models import AppKeyReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppKeysQuery(Query[Optional[Page[AppKeyReadModel]]]):
    """Keys of an app in id order; `None` if the app does not exist. Requires
    `app_keys:read` on the app's organization."""

    app_id: ObjectId
    page: PageRequest = PageRequest()
