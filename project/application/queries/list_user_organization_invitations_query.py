from typing import Optional

from project.application.queries.base import Query
from project.application.queries.list_organization_invitations_query import (
    OrganizationInvitationSort,
)
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import TrackableCriteria
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListUserOrganizationInvitationsQuery(
    Query[Page[OrganizationInvitationDetailReadModel]]
):
    """Organization invitations addressed to the email of `user_id`; the actor
    must be that user."""

    user_id: ObjectId
    sort: Optional[OrganizationInvitationSort] = None
    trackable: TrackableCriteria = TrackableCriteria()
    page: PageRequest = PageRequest()
