from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class RequestOrganizationVerificationCommandResult(CommandResult):
    id: ObjectId


class RequestOrganizationVerificationCommand(
    CommandWithResult[RequestOrganizationVerificationCommandResult]
):
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
