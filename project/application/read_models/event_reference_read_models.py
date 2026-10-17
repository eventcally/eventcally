from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.event_ref_read_model import EventRefReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class EventReferenceReadModel(BaseReadModel):
    """A reference of `event` by the organization `admin_unit`."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
    rating: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    event: EventRefReadModel
    admin_unit: OrganizationRefReadModel
    audit: Optional[AuditReadModel] = None  # get queries only
