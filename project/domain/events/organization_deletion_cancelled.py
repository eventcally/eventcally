from project.domain.events.base import Event
from project.domain.types import ObjectId


class OrganizationDeletionCancelled(Event):
    id: ObjectId
