from project.domain.types import ObjectId

from .base import Command


class DeleteEventCommand(Command):
    id: ObjectId
