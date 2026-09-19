from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.types import ObjectId

from .base import Event


class EventReferenceRequestReviewed(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
    review_status: EventReferenceRequestReviewStatus
