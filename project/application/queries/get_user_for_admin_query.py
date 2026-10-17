from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.user_admin_read_models import UserAdminReadModel
from project.domain.types.object_id import ObjectId


class GetUserForAdminQuery(Query[Optional[UserAdminReadModel]]):
    """The user with their role names, or `None`. Platform admins only."""

    id: ObjectId
