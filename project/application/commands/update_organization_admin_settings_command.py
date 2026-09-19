from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import Unsetable

from .base import Command


class UpdateOrganizationAdminSettingsCommand(Command):
    id: ObjectId
    incoming_reference_requests_allowed: Unsetable[bool] = UnsetField()
    can_create_other: Unsetable[bool] = UnsetField()
    can_invite_other: Unsetable[bool] = UnsetField()
    can_verify_other: Unsetable[bool] = UnsetField()
