from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.organization_verification_request_read_models import (
    OrganizationVerificationRequestReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOutgoingOrganizationVerificationRequestsQuery(
    Query[Optional[Page[OrganizationVerificationRequestReadModel]]]
):
    """The organization's own verification requests, newest first; `None` if the
    organization does not exist. Requires
    `outgoing_organization_verification_requests:read`."""

    admin_unit_id: ObjectId
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
