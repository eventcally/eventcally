from typing import List, Optional

from pydantic import Field

from project.application.queries.base import Query
from project.application.read_models.event_read_models import EventDetailReadModel
from project.domain.types.object_id import ObjectId


class ListDumpEventsQuery(Query[List[EventDetailReadModel]]):
    """One keyset batch (by id) of events for the data dumps. For trusted jobs: no actor check."""

    admin_unit_id: Optional[ObjectId] = None
    # Only published events of verified organizations (the full dump).
    public_only: bool = False
    after_id: int = Field(default=0, ge=0)
    limit: int = Field(default=200, ge=1, le=1000)
