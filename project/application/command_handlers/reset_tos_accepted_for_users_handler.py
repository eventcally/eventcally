from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .authorization_utils import ensure_actor_is_platform_admin


class ResetTosAcceptedForUsersHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.ResetTosAcceptedForUsersCommand, uow: AbstractUnitOfWork
    ):
        ensure_actor_is_platform_admin(cmd.actor, uow)

        return uow.users.reset_tos_accepted_for_all()
