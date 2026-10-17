from typing import List

from project.application.queries.base import Query
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberRoleReadModel,
)


class ListOrganizationMemberRolesQuery(Query[List[OrganizationMemberRoleReadModel]]):
    """All member roles ordered by id (role choices of member forms)."""
