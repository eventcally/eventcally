from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_admin_read_models import (
    OrganizationAdminReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationForAdminQuery(Query[Optional[OrganizationAdminReadModel]]):
    """`None` if the organization does not exist. Platform admins only."""

    id: ObjectId
