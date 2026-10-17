from typing import List

from project.application.queries.base import Query
from project.application.read_models.current_organization_read_models import (
    CurrentOrganizationReadModel,
)


class ListManageableOrganizationsQuery(Query[List[CurrentOrganizationReadModel]]):
    """The organizations the actor manages: all for platform admins, else the ones they
    are a member of (membership order). Empty for anonymous actors and installations."""

    # Only the organizations the actor is a member of (platform admins included).
    member_only: bool = False
