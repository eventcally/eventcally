from project.domain.types import ObjectId

from .base import Command


class RequestUserDeletionCommand(Command):
    id: ObjectId
