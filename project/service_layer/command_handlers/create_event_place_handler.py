from project.domain import commands, events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.models import EventPlace

from .abstract_command_handler import AbstractCommandHandler


class CreateEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateEventPlaceCommand, uow: AbstractUnitOfWork):
        with uow:
            event_place = EventPlace.create(cmd)
            uow.event_places.add(event_place)
            uow.commit()

            # TODO: hack
            uow.get_first_pending_event_by_type(events.EventPlaceCreated).id = (
                event_place.id
            )

            return commands.CreateEventPlaceCommandResult(id=event_place.id)
