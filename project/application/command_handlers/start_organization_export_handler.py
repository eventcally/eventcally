from project.application import commands
from project.application.services.abstract_organization_export_dispatcher import (
    AbstractOrganizationExportDispatcher,
)
from project.application.services.organization_export_jobs import (
    new_organization_export_job_id,
)
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class StartOrganizationExportHandler(AbstractCommandHandler):
    def __init__(self, dispatcher: AbstractOrganizationExportDispatcher):
        super().__init__()
        self.dispatcher = dispatcher

    def handle(
        self, cmd: commands.StartOrganizationExportCommand, uow: AbstractUnitOfWork
    ):
        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, cmd.admin_unit_id, "export:read", uow
        )

        job_id = new_organization_export_job_id(cmd.admin_unit_id)
        tracked = self.dispatcher.start(cmd.admin_unit_id, job_id)

        return commands.StartOrganizationExportCommandResult(
            job_id=job_id if tracked else None
        )
