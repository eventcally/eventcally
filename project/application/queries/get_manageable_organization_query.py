from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetManageableOrganizationQuery(Query[Optional[CurrentOrganizationReadModel]]):
    """The organization if the actor manages it (platform admin or member), else
    `None`."""

    id: ObjectId
