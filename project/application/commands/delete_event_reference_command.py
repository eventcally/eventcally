from project.domain.types import ObjectId

from .base import Command


class DeleteEventReferenceCommand(Command):
    id: ObjectId
