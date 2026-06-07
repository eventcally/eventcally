from typing import Optional

from project.domain.types import ObjectId
from project.domain.types.changed_value import ChangedValue
from project.domain.types.optional_changed_value_field_factory import (
    OptionalChangedValueField,
)

from .base import Event


class AppInstallationPermissionsUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
    permissions: Optional[ChangedValue[list[str]]] = OptionalChangedValueField()
