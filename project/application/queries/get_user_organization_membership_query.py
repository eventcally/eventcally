from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_member_read_models import (
    UserOrganizationMembershipReadModel,
)
from project.domain.types.object_id import ObjectId


class GetUserOrganizationMembershipQuery(
    Query[Optional[UserOrganizationMembershipReadModel]]
):
    """`None` if the membership does not exist; the actor must be its user."""

    id: ObjectId
