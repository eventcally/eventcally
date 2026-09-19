from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable

from .base import Command


class UpdateOrganizationWidgetSettingsCommand(Command):
    id: ObjectId
    widget_font: NullableUnsetable[str] = UnsetField()
    widget_background_color: NullableUnsetable[str] = UnsetField()
    widget_primary_color: NullableUnsetable[str] = UnsetField()
    widget_link_color: NullableUnsetable[str] = UnsetField()
