from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationMemberQuery(Query[Optional[OrganizationMemberReadModel]]):
    """`None` if the member does not exist. Requires `organization_members:read` on
    the member's organization."""

    id: ObjectId
