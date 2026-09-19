from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class RequestEventReferenceCommandResult(CommandResult):
    id: ObjectId
    verified: bool


class RequestEventReferenceCommand(
    CommandWithResult[RequestEventReferenceCommandResult]
):
    admin_unit_id: ObjectId
    event_id: ObjectId
