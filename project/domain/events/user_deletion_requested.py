from project.domain.types import ObjectId

from .base import Event


class UserDeletionRequested(Event):
    id: ObjectId
