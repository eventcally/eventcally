from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class AppKeyReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    oauth2_client_id: ObjectId
    kid: str
    checksum: str
    audit: Optional[AuditReadModel] = None  # get queries only


class WebhookEventRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: Optional[ObjectId] = None
    event_type: str
    timestamp: Optional[datetime] = None


class AppInstallationRefReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit: OrganizationRefReadModel
    permissions: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AppWebhookDeliveryReadModel(BaseReadModel):
    """A webhook delivery of an app as its manage pages show it; `admin_unit_id` is
    the app's organization."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    app_id: ObjectId
    admin_unit_id: ObjectId
    webhook_event: WebhookEventRefReadModel
    app_installation: Optional[AppInstallationRefReadModel] = None


class AppWebhookDeliveryAttemptReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    webhook_delivery_id: ObjectId
    app_id: ObjectId
    admin_unit_id: ObjectId
    url: Optional[str] = None
    status: Optional[str] = None
    status_code: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
