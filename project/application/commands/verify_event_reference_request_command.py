from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class VerifyEventReferenceRequestCommandResult(CommandResult):
    reference_id: ObjectId


class VerifyEventReferenceRequestCommand(
    CommandWithResult[VerifyEventReferenceRequestCommandResult]
):
    id: ObjectId
    rating: int = 50
    auto_verify: bool = False
