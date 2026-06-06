from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError

from .abstract_command_handler import AbstractCommandHandler


class UpdateAppInstallationPermissionsHandler(AbstractCommandHandler):
    def handle(
        self,
        cmd: commands.UpdateAppInstallationPermissionsCommand,
        uow: AbstractUnitOfWork,
    ):
        with uow:
            app_installation = uow.organization_app_installations.get(cmd.id)

            if not app_installation:
                raise NotFoundError(f"App installation with id {cmd.id} not found")

            app_installation.update_permissions(cmd.actor, cmd.permissions)
            uow.organization_app_installations.update(app_installation)
            uow.commit()
