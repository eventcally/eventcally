from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import Unsetable

from .base import Command


class UpdateOrganizationRelationCommand(Command):
    id: ObjectId
    auto_verify_event_reference_requests: Unsetable[bool] = UnsetField()
    verify: Unsetable[bool] = UnsetField()
