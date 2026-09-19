from project.domain.types import ObjectId

from .base import Event


class EventReferenceRequestAutoVerified(Event):
    id: ObjectId
    admin_unit_id: ObjectId
    event_id: ObjectId
