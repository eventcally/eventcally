from project.domain.types import ObjectId

from .base import Command


class DeleteEventOrganizerCommand(Command):
    id: ObjectId
