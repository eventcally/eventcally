from typing import List, Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.organization_read_models import (
    OrganizationListItemReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class SearchOrganizationsQuery(Query[Page[OrganizationListItemReadModel]]):
    """Public organization search. `keyword` matches name or short name (prefix
    matches first), `postal_codes` are location prefixes; unverified organizations
    only with `include_unverified` (the caller decides who may see them)."""

    keyword: Optional[str] = None
    postal_codes: List[str] = []
    include_unverified: bool = False
    only_verifier: bool = False
    reference_request_for_admin_unit_id: Optional[ObjectId] = None
    incoming_verification_requests_postal_code: Optional[str] = None
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
