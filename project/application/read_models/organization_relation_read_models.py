from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class OrganizationRelationReadModel(BaseReadModel):
    """A relation of `source_admin_unit_id` to `target_admin_unit`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    verify: bool = False
    auto_verify_event_reference_requests: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_modified_at: Optional[datetime] = None
    source_admin_unit: OrganizationRefReadModel
    target_admin_unit: OrganizationRefReadModel
    audit: Optional[AuditReadModel] = None  # get queries only
