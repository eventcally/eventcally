from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class OrganizationAdminReadModel(BaseReadModel):
    """An organization as the platform admin area lists and edits it."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    is_verified: bool = False
    created_at: Optional[datetime] = None
    deletion_requested_at: Optional[datetime] = None
    incoming_reference_requests_allowed: bool = False
    can_create_other: bool = False
    can_invite_other: bool = False
    can_verify_other: bool = False
    audit: Optional[AuditReadModel] = None  # get queries only
