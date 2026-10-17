from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_reference_read_models import (
    EventReferenceReadModel,
)
from project.domain.types.object_id import ObjectId


class GetEventReferenceQuery(Query[Optional[EventReferenceReadModel]]):
    """`None` if the reference does not exist. Public (the API detail only
    requires API access)."""

    id: ObjectId
