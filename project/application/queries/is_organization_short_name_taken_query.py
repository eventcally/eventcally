from typing import Optional

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class IsOrganizationShortNameTakenQuery(Query[bool]):
    """Whether another organization has the short name (case-insensitive)."""

    short_name: str
    exclude_id: Optional[ObjectId] = None
