from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.domain.types.object_id import ObjectId


class GetOutgoingEventReferenceRequestQuery(
    Query[Optional[EventReferenceRequestReadModel]]
):
    """`None` if the request does not exist. Requires
    `outgoing_event_reference_requests:read` on the event's organization."""

    id: ObjectId
