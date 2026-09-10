from typing import Any, Dict

from project.domain.types import ObjectId
from project.domain.types.unset_field_factory import UnsetField
from project.domain.types.unsetable import NullableUnsetable, Unsetable

from .base import Command


class UpdateCustomWidgetCommand(Command):
    id: ObjectId
    widget_type: Unsetable[str] = UnsetField()
    name: Unsetable[str] = UnsetField()
    settings: NullableUnsetable[Dict[str, Any]] = UnsetField()
