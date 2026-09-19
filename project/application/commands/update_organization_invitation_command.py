from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateOrganizationInvitationCommand(Command):
    id: ObjectId
    admin_unit_name: NullableUnsetable[str] = UnsetField()
    relation_auto_verify_event_reference_requests: Unsetable[bool] = UnsetField()
    relation_verify: Unsetable[bool] = UnsetField()
