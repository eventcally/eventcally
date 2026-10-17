from typing import Optional

from project.application.queries.api_key_sort import ApiKeySort
from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.api_key_read_models import ApiKeyReadModel
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOrganizationApiKeysQuery(Query[Optional[Page[ApiKeyReadModel]]]):
    """API keys of an organization; `None` if the organization does not exist.
    Requires `api_keys:read`."""

    admin_unit_id: ObjectId
    sort: Optional[ApiKeySort] = None
    page: PageRequest = PageRequest()
