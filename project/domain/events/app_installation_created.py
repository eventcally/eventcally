from project.domain.types import ObjectId

from .base import Event


class AppInstallationCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
    permissions: list[str]
