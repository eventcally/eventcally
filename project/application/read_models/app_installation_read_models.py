from datetime import datetime
from typing import List, Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_member_read_models import (
    UserOrganizationMembershipReadModel,
)
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class InstallableAppReadModel(BaseReadModel):
    """What an organization sees of another organization's app when installing it
    (no credentials)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    client_name: Optional[str] = None
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    description: Optional[str] = None
    app_permissions: List[str] = []


class AppInstallationReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    oauth2_client_id: ObjectId
    permissions: List[str] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    admin_unit: Optional[OrganizationRefReadModel] = None
    oauth2_client: InstallableAppReadModel
    audit: Optional[AuditReadModel] = None  # get queries only


class UserAppInstallationReadModel(BaseReadModel):
    """An installation of the requesting app in one of the user's organizations,
    with the user's membership there."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    admin_unit: OrganizationRefReadModel
    membership: Optional[UserOrganizationMembershipReadModel] = None
