from project.domain.types import ObjectId

from .base import Event


class EventReferenceRequestCreated(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
