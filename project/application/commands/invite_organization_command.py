from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class InviteOrganizationCommandResult(CommandResult):
    id: ObjectId


class InviteOrganizationCommand(CommandWithResult[InviteOrganizationCommandResult]):
    admin_unit_id: ObjectId
    email: str
    admin_unit_name: Optional[str] = None
    relation_auto_verify_event_reference_requests: bool = False
    relation_verify: bool = False
