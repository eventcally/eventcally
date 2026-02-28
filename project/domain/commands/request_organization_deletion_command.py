from project.domain.types import ObjectId

from .base import Command


class RequestOrganizationDeletionCommand(Command):
    id: ObjectId
