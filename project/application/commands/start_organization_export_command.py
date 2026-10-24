from typing import Optional

from project.domain.types import ObjectId

from .base import CommandResult, CommandWithResult


class StartOrganizationExportCommandResult(CommandResult):
    job_id: Optional[str] = None


class StartOrganizationExportCommand(
    CommandWithResult[StartOrganizationExportCommandResult]
):
    admin_unit_id: ObjectId
