from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class OrganizationInvitationListItemReadModel(BaseReadModel):
    """A row of the manage list and of the API list
    (`OrganizationInvitationListRefSchema`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    admin_unit_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None


class OrganizationInvitationDetailReadModel(BaseReadModel):
    """The API detail (`OrganizationInvitationSchema`); `admin_unit` feeds its
    `organization`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    email: str
    admin_unit_id: ObjectId
    admin_unit_name: Optional[str] = None
    relation_auto_verify_event_reference_requests: bool = False
    relation_verify: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    admin_unit: OrganizationRefReadModel
    audit: Optional[AuditReadModel] = None  # get queries only
