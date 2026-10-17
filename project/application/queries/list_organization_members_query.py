from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOrganizationMembersQuery(Query[Optional[Page[OrganizationMemberReadModel]]]):
    """Members of an organization ordered by email (case-insensitive); `None` if the
    organization does not exist. Requires `organization_members:read`."""

    admin_unit_id: ObjectId
    page: PageRequest = PageRequest()
