from project.application import commands
from project.application.command_handlers.app_utils import ensure_app_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app = ensure_app_exists(cmd.id, uow)
            app.delete_app(cmd.actor)
            uow.apps.remove(app)
            uow.commit()
