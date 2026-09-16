from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .app_key_utils import ensure_app_key_exists
from .authorization_utils import ensure_actor_has_permission_for_admin_unit


class DeleteAppKeyHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteAppKeyCommand, uow: AbstractUnitOfWork):
        app_key = ensure_app_key_exists(cmd.id, uow)

        ensure_actor_has_permission_for_admin_unit(
            cmd.actor, app_key.admin_unit_id, "app_keys:write", uow
        )

        app_key.delete(cmd.actor)
        uow.app_keys.remove(app_key)
