from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.oauth2_client_read_models import AppReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListAppsQuery(Query[Optional[Page[AppReadModel]]]):
    """Apps of an organization in id order; `None` if the organization does not
    exist. Requires `apps:read`."""

    admin_unit_id: ObjectId
    page: PageRequest = PageRequest()
