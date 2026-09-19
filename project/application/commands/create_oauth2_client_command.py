from typing import List, Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateOAuth2ClientCommandResult(CommandResult):
    id: ObjectId
    client_id: str
    client_secret: str


class CreateOAuth2ClientCommand(CommandWithResult[CreateOAuth2ClientCommandResult]):
    name: str
    redirect_uris: List[str] = []
    scope: Optional[str] = None
    user_id: Optional[ObjectId] = None
    admin_unit_id: Optional[ObjectId] = None
