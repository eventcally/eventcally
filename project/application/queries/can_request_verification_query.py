from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class CanRequestVerificationQuery(Query[bool]):
    """Whether `source` may ask `target` for verification: another organization that
    verifies others, accepts incoming requests and serves the source's postal code."""

    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
