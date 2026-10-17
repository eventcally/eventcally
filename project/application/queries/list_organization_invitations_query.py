from enum import Enum
from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import TrackableCriteria
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationListItemReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class OrganizationInvitationSort(str, Enum):
    """Values equal the API `sort` strings."""

    created_at_desc = "-created_at"
    updated_at_desc = "-updated_at"
    last_modified_at_desc = "-last_modified_at"


class ListOrganizationInvitationsQuery(
    Query[Optional[Page[OrganizationInvitationListItemReadModel]]]
):
    """Invitations sent by an organization; `None` if the organization does not
    exist. Requires `organization_invitations:read`."""

    admin_unit_id: ObjectId
    sort: Optional[OrganizationInvitationSort] = None
    trackable: TrackableCriteria = TrackableCriteria()
    page: PageRequest = PageRequest()
