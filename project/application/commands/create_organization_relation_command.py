from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class CreateOrganizationRelationCommandResult(CommandResult):
    id: ObjectId


class CreateOrganizationRelationCommand(
    CommandWithResult[CreateOrganizationRelationCommandResult]
):
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    auto_verify_event_reference_requests: bool = False
    verify: bool = False
