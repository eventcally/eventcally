from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.service_layer.command_handlers.app_utils import ensure_app_exists

from .abstract_command_handler import AbstractCommandHandler


class DeleteAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteAppCommand, uow: AbstractUnitOfWork):
        with uow:
            app = ensure_app_exists(cmd.id, uow)
            app.delete_app(cmd)
            uow.apps.remove(app)
            uow.commit()
