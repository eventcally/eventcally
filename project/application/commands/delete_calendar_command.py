from project.domain.types import ObjectId

from .base import Command


class DeleteCalendarCommand(Command):
    id: ObjectId
