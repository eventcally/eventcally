from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class AnyOrganizationAcceptsReferenceRequestsQuery(Query[bool]):
    """Whether an organization other than `exclude_admin_unit_id` accepts incoming
    reference requests."""

    exclude_admin_unit_id: ObjectId
