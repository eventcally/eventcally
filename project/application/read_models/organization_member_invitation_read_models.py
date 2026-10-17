from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class OrganizationMemberInvitationReadModel(BaseReadModel):
    """A member invitation as the manage pages and the invited user see it. `roles`
    stays the comma-separated role names the update form splits."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    email: str
    roles: Optional[str] = None
    admin_unit: OrganizationRefReadModel
