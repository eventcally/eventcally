from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable

from .base import Command


class UpdateUserGeneralSettingsCommand(Command):
    id: ObjectId
    locale: NullableUnsetable[str] = UnsetField()
