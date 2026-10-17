from typing import Optional

from project.application.queries.base import Query
from project.application.queries.organization_relation_sort import (
    OrganizationRelationSort,
)
from project.application.queries.page_request import PageRequest
from project.application.read_models.organization_relation_read_models import (
    OrganizationRelationReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class ListOutgoingOrganizationRelationsQuery(
    Query[Optional[Page[OrganizationRelationReadModel]]]
):
    """Relations of the organization to others; `keyword` matches the target
    organization's name (`parse_like_term`). `None` if the organization does not
    exist. Requires `outgoing_organization_relations:read`."""

    admin_unit_id: ObjectId
    keyword: Optional[str] = None
    verify: Optional[bool] = None
    auto_verify_event_reference_requests: Optional[bool] = None
    sort: Optional[OrganizationRelationSort] = None
    page: PageRequest = PageRequest()
