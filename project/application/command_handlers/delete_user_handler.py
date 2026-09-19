from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin
from .user_utils import ensure_user_exists


class DeleteUserHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteUserCommand, uow: AbstractUnitOfWork):
        user = ensure_user_exists(cmd.id, uow)

        ensure_actor_is_platform_admin(cmd.actor, uow)

        user.delete(cmd.actor)
        uow.users.remove(user)
