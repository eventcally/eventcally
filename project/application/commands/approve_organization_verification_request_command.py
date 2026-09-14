from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class ApproveOrganizationVerificationRequestCommandResult(CommandResult):
    id: ObjectId


class ApproveOrganizationVerificationRequestCommand(
    CommandWithResult[ApproveOrganizationVerificationRequestCommandResult]
):
    id: ObjectId
    auto_verify_event_reference_requests: Optional[bool] = None
