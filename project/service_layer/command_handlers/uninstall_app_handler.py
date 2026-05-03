from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError

from .abstract_command_handler import AbstractCommandHandler


class UninstallAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UninstallAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app_installation = uow.apps.get_app_installation(cmd.id)

            if not app_installation:
                raise NotFoundError(f"App installation with id {cmd.id} not found")

            app_installation.uninstall(cmd)
            uow.apps.remove_app_installation(app_installation)
            uow.commit()
