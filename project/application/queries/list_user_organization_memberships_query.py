from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.read_models.organization_member_read_models import (
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListUserOrganizationMembershipsQuery(
    Query[Page[UserOrganizationMembershipReadModel]]
):
    """The memberships of `user_id`; the actor must be that user."""

    user_id: ObjectId
    page: PageRequest = PageRequest()
