from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_member_read_models import (
    OrganizationMemberReadModel,
)
from project.application.read_models.organization_read_models import (
    OrganizationDetailReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.models.enums.organization_verification_request_rejection_reason import (
    OrganizationVerificationRequestRejectionReason,
)
from project.domain.models.enums.organization_verification_request_review_status import (
    OrganizationVerificationRequestReviewStatus,
)
from project.domain.types.object_id import ObjectId


class OrganizationVerificationRequestReadModel(BaseReadModel):
    """A request of `source_admin_unit` to be verified by `target_admin_unit`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    review_status: OrganizationVerificationRequestReviewStatus
    rejection_reason: Optional[OrganizationVerificationRequestRejectionReason] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    source_admin_unit: OrganizationRefReadModel
    target_admin_unit: OrganizationRefReadModel
    audit: Optional[AuditReadModel] = None  # get queries only


class VerificationReviewOrganizationReadModel(OrganizationDetailReadModel):
    """The requesting organization as the reviewer sees it, with its members."""

    logo_id: Optional[ObjectId] = None
    members: List[OrganizationMemberReadModel] = []


class OrganizationVerificationRequestReviewReadModel(BaseReadModel):
    """The incoming request on the review page."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    review_status: OrganizationVerificationRequestReviewStatus
    source_admin_unit: VerificationReviewOrganizationReadModel
