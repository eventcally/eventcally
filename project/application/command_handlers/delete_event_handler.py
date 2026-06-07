from project.application import commands
from project.application.command_handlers.event_utils import ensure_event_exists
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler


class DeleteEventHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteEventCommand, uow: AbstractUnitOfWork):
        with uow:
            event = ensure_event_exists(cmd.id, uow)
            event.delete(cmd.actor)
            uow.events.remove(event)
            uow.commit()
