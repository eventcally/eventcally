from project.domain.types import ObjectId

from .base import Command


class CancelUserDeletionCommand(Command):
    id: ObjectId
