from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateEventReferenceCommandResult(CommandResult):
    id: ObjectId


class CreateEventReferenceCommand(CommandWithResult[CreateEventReferenceCommandResult]):
    admin_unit_id: ObjectId
    event_id: ObjectId
    rating: int = 50
