from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class HasOtherAdminQuery(Query[bool]):
    """Whether the organization has an admin member other than `user_id`."""

    admin_unit_id: ObjectId
    user_id: ObjectId
