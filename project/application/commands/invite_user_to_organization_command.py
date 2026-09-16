from typing import List

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class InviteUserToOrganizationCommandResult(CommandResult):
    id: ObjectId


class InviteUserToOrganizationCommand(
    CommandWithResult[InviteUserToOrganizationCommandResult]
):
    admin_unit_id: ObjectId
    email: str
    roles: List[str] = []
