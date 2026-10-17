from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.organization_admin_read_models import (
    OrganizationAdminReadModel,
)
from project.application.read_models.page import Page


class ListOrganizationsForAdminQuery(Query[Page[OrganizationAdminReadModel]]):
    """All organizations by name; `keyword` uses `parse_like_term`. Platform admins
    only."""

    keyword: Optional[str] = None
    page: PageRequest = PageRequest()
