from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork

from .abstract_command_handler import AbstractCommandHandler
from .event_place_utils import ensure_event_place_exists


class DeleteEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.DeleteEventPlaceCommand, uow: AbstractUnitOfWork):
        with uow:
            event_place = ensure_event_place_exists(cmd.id, uow)
            event_place.delete(cmd.actor)
            uow.event_places.remove(event_place)
            uow.commit()
