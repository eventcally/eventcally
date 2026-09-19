from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable

from .base import Command


class UpdateSettingsCommand(Command):
    tos: NullableUnsetable[str] = UnsetField()
    legal_notice: NullableUnsetable[str] = UnsetField()
    contact: NullableUnsetable[str] = UnsetField()
    privacy: NullableUnsetable[str] = UnsetField()
    start_page: NullableUnsetable[str] = UnsetField()
    announcement: NullableUnsetable[str] = UnsetField()
