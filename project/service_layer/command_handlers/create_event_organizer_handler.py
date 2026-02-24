from project.domain import commands, events
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.models import EventOrganizer

from .abstract_command_handler import AbstractCommandHandler


class CreateEventOrganizerHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CreateEventOrganizerCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            event_organizer = EventOrganizer.create(cmd)
            uow.event_organizers.add(event_organizer)
            uow.commit()

            # TODO: hack
            uow.get_first_pending_event_by_type(events.EventOrganizerCreated).id = (
                event_organizer.id
            )

            return commands.CreateEventOrganizerCommandResult(id=event_organizer.id)
