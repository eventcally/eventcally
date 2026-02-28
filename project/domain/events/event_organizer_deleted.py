from project.domain.types import ObjectId

from .base import Event


class EventOrganizerDeleted(Event):
    id: ObjectId
