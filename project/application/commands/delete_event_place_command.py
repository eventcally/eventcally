from project.domain.types import ObjectId

from .base import Command


class DeleteEventPlaceCommand(Command):
    id: ObjectId
