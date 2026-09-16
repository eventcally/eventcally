from typing import Optional

from project.domain.models.enums.event_reference_request_rejection_reason import (
    EventReferenceRequestRejectionReason,
)
from project.domain.types import ObjectId

from .base import Command


class RejectEventReferenceRequestCommand(Command):
    id: ObjectId
    rejection_reason: Optional[EventReferenceRequestRejectionReason] = None
    auto_verify: bool = False
