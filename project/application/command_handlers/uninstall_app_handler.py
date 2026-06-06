from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError

from .abstract_command_handler import AbstractCommandHandler


class UninstallAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UninstallAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app_installation = uow.organization_app_installations.get(cmd.id)

            if not app_installation:
                raise NotFoundError(f"App installation with id {cmd.id} not found")

            app_installation.delete(cmd.actor)
            uow.organization_app_installations.remove(app_installation)
            uow.commit()
