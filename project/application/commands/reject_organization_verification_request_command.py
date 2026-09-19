from typing import Optional

from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.types import ObjectId

from .base import Command


class RejectOrganizationVerificationRequestCommand(Command):
    id: ObjectId
    rejection_reason: Optional[OrganizationVerificationRequestRejectionReason] = None
