from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerRefReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventOrganizerRefQuery(Query[Optional[EventOrganizerRefReadModel]]):
    """The organizer if it belongs to the organization, else `None`."""

    admin_unit_id: ObjectId
    id: ObjectId
