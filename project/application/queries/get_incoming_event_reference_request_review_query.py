from typing import Optional

from project.application.queries.base import Query
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReviewReadModel,
)
from project.domain.types.object_id import ObjectId


class GetIncomingEventReferenceRequestReviewQuery(
    Query[Optional[EventReferenceRequestReviewReadModel]]
):
    """The request with its event for the review page, or `None`. Requires
    `incoming_event_reference_requests:read` on the reviewing organization."""

    id: ObjectId
