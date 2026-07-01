from project.domain.types import ObjectId
from project.domain.types.changed_value import ChangedValue

from .base import Event


class AppInstallationPermissionsUpdated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
    permissions: ChangedValue[set[str]]
