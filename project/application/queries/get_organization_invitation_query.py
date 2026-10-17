from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationInvitationQuery(
    Query[Optional[OrganizationInvitationDetailReadModel]]
):
    """`None` if the invitation does not exist. Requires
    `organization_invitations:read` on the invitation's organization."""

    id: ObjectId
