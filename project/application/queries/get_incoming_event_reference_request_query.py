from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.domain.types.object_id import ObjectId


class GetIncomingEventReferenceRequestQuery(
    Query[Optional[EventReferenceRequestReadModel]]
):
    """`None` if the request does not exist. Requires
    `incoming_event_reference_requests:read` on the requested organization."""

    id: ObjectId
