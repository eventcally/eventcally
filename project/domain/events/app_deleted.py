from project.domain.types import ObjectId

from .base import Event


class AppDeleted(Event):
    id: ObjectId
    admin_unit_id: ObjectId
