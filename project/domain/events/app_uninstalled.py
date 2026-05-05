from project.domain.types import ObjectId

from .base import Event


class AppUninstalled(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    app_id: ObjectId
