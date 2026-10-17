from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
)
from project.domain.types.object_id import ObjectId


class GetCurrentOrganizationQuery(Query[Optional[CurrentOrganizationReadModel]]):
    """The organization with the flags requests act on, or `None`. No authorization: it
    only loads the organization a decorator then checks the actor against."""

    id: ObjectId
