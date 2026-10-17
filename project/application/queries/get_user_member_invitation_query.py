from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_member_invitation_read_models import (
    OrganizationMemberInvitationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetUserMemberInvitationQuery(
    Query[Optional[OrganizationMemberInvitationReadModel]]
):
    """`None` if the invitation does not exist; the actor must be its recipient."""

    id: ObjectId
