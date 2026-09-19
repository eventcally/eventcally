from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin
from .user_utils import ensure_user_exists


class UpdateUserRolesHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.UpdateUserRolesCommand, uow: AbstractUnitOfWork):
        user = ensure_user_exists(cmd.id, uow)

        ensure_actor_is_platform_admin(cmd.actor, uow)

        user.update(actor=cmd.actor, roles=cmd.roles)
        uow.users.update(user)
