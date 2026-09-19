from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateApiKeyCommandResult(CommandResult):
    id: ObjectId
    key: str


class CreateApiKeyCommand(CommandWithResult[CreateApiKeyCommandResult]):
    name: str
    user_id: Optional[ObjectId] = None
    admin_unit_id: Optional[ObjectId] = None
