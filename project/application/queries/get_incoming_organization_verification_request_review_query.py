from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReviewReadModel,
)
from project.domain.types.object_id import ObjectId


class GetIncomingOrganizationVerificationRequestReviewQuery(
    Query[Optional[OrganizationVerificationRequestReviewReadModel]]
):
    """The request with the requesting organization's profile and members, or
    `None`. Requires `incoming_organization_verification_requests:read` on the
    target organization."""

    id: ObjectId
