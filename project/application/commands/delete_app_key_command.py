from project.domain.types import ObjectId

from .base import Command


class DeleteAppKeyCommand(Command):
    id: ObjectId
