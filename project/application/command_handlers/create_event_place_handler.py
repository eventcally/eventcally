from project.application import commands
from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.models.aggregates.event_place_aggregate import EventPlaceAggregate
from project.domain.models.entities.image_entity import ImageEntity

from .abstract_command_handler import AbstractCommandHandler


class CreateEventPlaceHandler(AbstractCommandHandler):
    def handle(self, cmd: commands.CreateEventPlaceCommand, uow: AbstractUnitOfWork):
        with uow:
            event_place = EventPlaceAggregate.create(
                actor=cmd.actor,
                admin_unit_id=cmd.admin_unit_id,
                name=cmd.name,
                url=cmd.url,
                description=cmd.description,
                location=cmd.location,
                photo=ImageEntity.from_value_object(cmd.photo) if cmd.photo else None,
            )
            uow.event_places.add(event_place)
            uow.commit()

            return commands.CreateEventPlaceCommandResult(id=event_place.id)
