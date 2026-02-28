from project.domain.types import ObjectId

from .base import Event


class OrganizationDeletionRequested(Event):
    id: ObjectId
