from project.domain.types import ObjectId

from .base import Command


class RemoveEventFromCalendarCommand(Command):
    calendar_id: ObjectId
    event_id: ObjectId
