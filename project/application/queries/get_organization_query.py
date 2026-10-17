from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.organization_read_models import (
    OrganizationDetailReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOrganizationQuery(Query[Optional[OrganizationDetailReadModel]]):
    """The public organization profile, or `None`."""

    id: ObjectId
