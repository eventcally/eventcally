from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteUserDueForDeletionHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteUserDueForDeletionCommand, uow: AbstractUnitOfWork
    ) -> bool:
        """Skips (returns False) users that are gone or whose deletion request was
        cancelled or is still within the grace period."""
        user = uow.users.get(cmd.user_id)

        if user is None or not user.is_deletion_due():
            return False

        user.delete(cmd.actor)
        uow.users.remove(user)
        return True
