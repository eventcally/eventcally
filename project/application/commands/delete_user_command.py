from project.domain.types import ObjectId

from .base import Command


class DeleteUserCommand(Command):
    id: ObjectId
