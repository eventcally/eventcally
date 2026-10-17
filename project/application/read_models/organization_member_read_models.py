from typing import List

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.application.read_models.user_ref_read_model import UserRefReadModel
from project.domain.types.object_id import ObjectId


class OrganizationMemberRoleReadModel(BaseReadModel):
    """`title` is an English msgid; displays and form choices translate it."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    title: str


class OrganizationMemberReadModel(BaseReadModel):
    """A member as the manage list, update form and delete page show it. Roles are
    ordered by role id."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    user_id: ObjectId
    user: UserRefReadModel
    roles: List[OrganizationMemberRoleReadModel] = []


class UserOrganizationMembershipReadModel(BaseReadModel):
    """One of the current user's memberships (profile list and leave page)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    user_id: ObjectId
    is_admin: bool = False
    admin_unit: OrganizationRefReadModel
