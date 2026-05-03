from typing import Optional

from pydantic import Field

from project.domain.commands.create_webhook import CreateWebhook
from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateAppCommandResult(CommandResult):
    id: ObjectId


class CreateAppCommand(CommandWithResult[CreateAppCommandResult]):
    admin_unit_id: ObjectId
    name: str
    app_permissions: list[str] = Field(min_length=1)
    redirect_uris: Optional[list[str]] = None
    scope: Optional[str] = None
    description: Optional[str] = None
    homepage_url: Optional[str] = None
    setup_url: Optional[str] = None
    webhook: Optional[CreateWebhook] = None
