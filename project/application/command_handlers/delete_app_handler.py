from project.application import commands
from project.application.command_handlers.app_utils import ensure_app_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class DeleteAppHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteAppCommand, uow: AbstractUnitOfWork):
        app = ensure_app_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, app.admin_unit_id, "apps:write", uow
        )

        app.delete_app(cmd.actor)
        uow.apps.remove(app)
