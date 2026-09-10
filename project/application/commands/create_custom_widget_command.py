from typing import Any, Dict, Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateCustomWidgetCommandResult(CommandResult):
    id: ObjectId


class CreateCustomWidgetCommand(CommandWithResult[CreateCustomWidgetCommandResult]):
    admin_unit_id: ObjectId
    widget_type: str
    name: str
    settings: Optional[Dict[str, Any]] = None
