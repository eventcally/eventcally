from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.domain.types import ObjectId

from .base import Event


class OrganizationVerificationRequestReviewed(Event):
    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    review_status: OrganizationVerificationRequestReviewStatus
