from typing import List

from project.application.queries.base import Query
from project.application.read_models.user_admin_read_models import RoleReadModel


class ListRolesQuery(Query[List[RoleReadModel]]):
    """All roles by id. Platform admins only."""

    pass
