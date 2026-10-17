from typing import Optional

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class IsOrganizationNameTakenQuery(Query[bool]):
    """Whether another organization has the name (case-insensitive)."""

    name: str
    exclude_id: Optional[ObjectId] = None
