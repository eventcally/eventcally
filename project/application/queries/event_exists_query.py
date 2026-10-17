from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class EventExistsQuery(Query[bool]):
    """Whether the event exists (no authorization: it answers nothing about it)."""

    id: ObjectId
