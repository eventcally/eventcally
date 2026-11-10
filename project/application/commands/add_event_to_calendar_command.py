from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class AddEventToCalendarCommandResult(CommandResult):
    id: ObjectId


class AddEventToCalendarCommand(CommandWithResult[AddEventToCalendarCommandResult]):
    calendar_id: ObjectId
    event_id: ObjectId
