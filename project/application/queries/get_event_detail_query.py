from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_read_models import EventDetailReadModel
from project.domain.types.object_id import ObjectId


class GetEventDetailQuery(Query[Optional[EventDetailReadModel]]):
    """The event with everything its page shows; `None` if unknown. Raises
    `UnauthorizedError` unless the actor may read it (published and verified, planned
    for planners, or `events:read`)."""

    id: ObjectId
    reference_admin_unit_id: Optional[ObjectId] = None
