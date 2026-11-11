from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateCalendarCommand(Command):
    id: ObjectId
    name: Unsetable[str] = UnsetField()
    description: NullableUnsetable[str] = UnsetField()
    private: Unsetable[bool] = UnsetField()
