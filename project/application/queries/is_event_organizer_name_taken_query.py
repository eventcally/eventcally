from typing import Optional

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class IsEventOrganizerNameTakenQuery(Query[bool]):
    """Whether another organizer of the organization has the name (case-insensitive)."""

    admin_unit_id: ObjectId
    name: str
    exclude_id: Optional[ObjectId] = None
