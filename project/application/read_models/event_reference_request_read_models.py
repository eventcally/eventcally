from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.event_read_models import (
    EventDateReadModel,
    EventDetailReadModel,
)
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.models.enums.event_reference_request_review_status import (
    EventReferenceRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId


class EventReferenceRequestReadModel(BaseReadModel):
    """A request to `admin_unit` to reference `event`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
    review_status: EventReferenceRequestReviewStatus
    rejection_reason: Optional[EventReferenceRequestRejectionReason] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    event: EventRefReadModel
    admin_unit: OrganizationRefReadModel
    audit: Optional[AuditReadModel] = None  # get queries only


class EventReferenceRequestReviewReadModel(EventReferenceRequestReadModel):
    """The review page: the request with the full event, its upcoming dates and
    whether the reviewing organization already auto-verifies the requester."""

    event: EventDetailReadModel
    upcoming_dates: List[EventDateReadModel] = []
    auto_verify: bool = False
