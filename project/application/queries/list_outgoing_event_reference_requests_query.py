from typing import Optional

from project.application.queries.base import Query
from project.application.queries.page_request import PageRequest
from project.application.queries.trackable_criteria import (
    TrackableCriteria,
    TrackableSort,
)
from project.application.read_models.event_reference_request_read_models import (
    EventReferenceRequestReadModel,
)
from project.application.read_models.page import Page
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId


class ListOutgoingEventReferenceRequestsQuery(
    Query[Optional[Page[EventReferenceRequestReadModel]]]
):
    """Requests for the organization's events, newest first; `None` if the
    organization does not exist. Requires `outgoing_event_reference_requests:read`."""

    admin_unit_id: ObjectId
    review_status: Optional[EventReferenceRequestReviewStatus] = None
    trackable: TrackableCriteria = TrackableCriteria()
    sort: Optional[TrackableSort] = None
    page: PageRequest = PageRequest()
