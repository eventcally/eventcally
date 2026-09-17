from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable

from .base import Command


class UpdatePlanningSettingsCommand(Command):
    planning_external_calendars: NullableUnsetable[str] = UnsetField()
