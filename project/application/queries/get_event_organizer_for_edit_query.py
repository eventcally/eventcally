from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_organizer_read_models import (
    EventOrganizerEditReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventOrganizerForEditQuery(Query[Optional[EventOrganizerEditReadModel]]):
    """`None` if the organizer does not exist. Fills the manage update form and backs the
    delete confirmation."""

    id: ObjectId
