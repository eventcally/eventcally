from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateCalendarCommandResult(CommandResult):
    id: ObjectId


class CreateCalendarCommand(CommandWithResult[CreateCalendarCommandResult]):
    admin_unit_id: ObjectId
    name: str
    description: Optional[str] = None
    private: bool = False
