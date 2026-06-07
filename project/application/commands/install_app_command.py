from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class InstallAppCommandResult(CommandResult):
    id: ObjectId


class InstallAppCommand(CommandWithResult[InstallAppCommandResult]):
    admin_unit_id: ObjectId
    app_id: ObjectId
