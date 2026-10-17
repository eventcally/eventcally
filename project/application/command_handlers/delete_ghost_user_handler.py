from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteGhostUserHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteGhostUserCommand, uow: AbstractUnitOfWork
    ) -> bool:
        """The ghost rule (never confirmed, old enough) is enforced by
        ListGhostUserIdsQuery; here only existence is checked."""
        user = uow.users.get(cmd.user_id)

        if user is None:
            return False

        user.delete(cmd.actor)
        uow.users.remove(user)
        return True
