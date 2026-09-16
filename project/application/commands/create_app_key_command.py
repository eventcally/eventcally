from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateAppKeyCommandResult(CommandResult):
    id: ObjectId
    private_pem: str


class CreateAppKeyCommand(CommandWithResult[CreateAppKeyCommandResult]):
    admin_unit_id: ObjectId
    app_id: ObjectId
