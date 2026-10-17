from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteOldEventHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.DeleteOldEventCommand, uow: AbstractUnitOfWork
    ) -> bool:
        """The age rule is enforced by ListOldEventIdsQuery; here only existence is
        checked. Deletes silently: no EventDeleted domain event, so no webhook per
        purged event (same as the raw delete this replaces)."""
        event = uow.events.get(cmd.event_id)

        if event is None:
            return False

        uow.events.remove(event)
        return True
