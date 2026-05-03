from project.domain.types import ObjectId

from .base import Command


class DeleteAppCommand(Command):
    id: ObjectId
