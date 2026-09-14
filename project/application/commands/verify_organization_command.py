from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class VerifyOrganizationCommandResult(CommandResult):
    id: ObjectId


class VerifyOrganizationCommand(CommandWithResult[VerifyOrganizationCommandResult]):
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    auto_verify_event_reference_requests: Optional[bool] = None
