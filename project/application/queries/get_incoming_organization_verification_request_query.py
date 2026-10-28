from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReadModel,
)
from project.domain.types.object_id import ObjectId


class GetIncomingOrganizationVerificationRequestQuery(
    Query[Optional[OrganizationVerificationRequestReadModel]]
):
    """`None` if the request does not exist. Requires
    `incoming_organization_verification_requests:read` on the reviewing
    organization."""

    id: ObjectId
