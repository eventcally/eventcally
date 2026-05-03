from project.domain.types import ObjectId

from .base import Event


class EventPlaceDeleted(Event):
    id: ObjectId
    admin_unit_id: ObjectId
