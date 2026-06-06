from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.event_organizer_aggregate import (
    EventOrganizerAggregate,
)
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler


class CreateEventOrganizerHandler(AbstractCommandHandler):
    def handle(
        self, cmd: commands.CreateEventOrganizerCommand, uow: AbstractUnitOfWork
    ):
        with uow:
            event_organizer = EventOrganizerAggregate.create(
                actor=cmd.actor,
                admin_unit_id=cmd.admin_unit_id,
                name=cmd.name,
                url=cmd.url,
                email=cmd.email,
                phone=cmd.phone,
                fax=cmd.fax,
                location=cmd.location,
                logo=ImageEntity.from_value_object(cmd.logo),
            )
            uow.event_organizers.add(event_organizer)
            uow.commit()

            return commands.CreateEventOrganizerCommandResult(id=event_organizer.id)
