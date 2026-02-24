from project.domain import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .event_organizer_utils import ensure_event_organizer_exists


class UpdateEventOrganizerHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.UpdateEventOrganizerCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            event_organizer = ensure_event_organizer_exists(cmd.id, uow)
            event_organizer.update(cmd)
            uow.commit()
